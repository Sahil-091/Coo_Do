# Campus Connect (placeholder name — see R&D doc Section 29)

Small, real-world actions toward student connection — not another mood
tracker, chatbot, or engagement-maximizing app. See
`RnD_Student_Connection_Platform.md` for the full research/rationale and
`Build_Prompt_Sequence.md` for the phase-by-phase build plan this repo
follows.

**Status: Phase 0 (infrastructure scaffold) complete.** No product
features exist yet on purpose — see the phase table below.

## Architecture at a glance

One responsive Next.js PWA (works on mobile and desktop from a single
codebase — see `frontend/`) talking to five independently-deployable
FastAPI services (`backend/services/*`), backed by one PostgreSQL
instance with **role-separated, least-privilege access** enforced by
Postgres itself, not just by application code.

```
campus-connect/
├── frontend/                  Next.js 16 + TS + Tailwind, installable PWA
│   └── src/
│       ├── app/                Routes (App Router)
│       ├── components/ui/      Design system (Phase 1)
│       ├── features/*/         One folder per product feature, phase-stamped
│       ├── safety/              ISOLATED module — see safety/README.md
│       ├── lib/                 API client, env validation
│       └── types/                Shared domain types
├── backend/
│   ├── db/                     Shared models + Alembic migrations
│   │   ├── models/core.py       Tables owned by core-api
│   │   ├── models/safety.py     Table owned by safety-service (safety_events)
│   │   ├── grants.sql            Least-privilege role setup — see below
│   │   └── migrations/
│   └── services/
│       ├── core-api/            Main app-facing API
│       ├── safety-service/      Crisis/safety classifier — see Section 10
│       ├── matching-service/    Phase 11
│       ├── moderation-service/  Phase 12
│       └── notification-service/ Opt-in, non-manipulative notifications
├── docker-compose.yml          Postgres + migrator + all 5 services
└── docs/schema-plan.md         Every deferred table and which phase adds it
```

## Why the safety/ and safety-service boundary is load-bearing

Per R&D doc Section 10: **the LLM is never the final decision-maker on
anything risk-adjacent.** Concretely in this codebase:

- Frontend: no feature module may implement its own crisis-detection
  logic. Everything routes through `frontend/src/safety/client.ts`.
- Backend: `safety-service` is the only thing with any database access
  to `safety_events`. This isn't a convention — it's enforced by a
  separate Postgres role (`app_safety_service`) that has **zero grants**
  on every other table, and `app_core_api` has **zero grants** on
  `safety_events`. Verified by hand during Phase 0 (see `db/grants.sql`
  for the exact grants; `alembic check` confirms the models match what's
  actually applied).

Phase 6 (AI Navigator) is not allowed to make its first LLM call until
Phase 5 (Crisis/Safety System) is built and reviewed. This ordering is
intentional, not arbitrary — see `Build_Prompt_Sequence.md`.

## Running locally

### Option A — Docker Compose (closest to production shape)

```bash
docker compose up -d postgres
docker compose run --rm migrate      # alembic upgrade head + grants.sql
docker compose up -d core-api safety-service matching-service moderation-service notification-service
cd frontend && cp .env.example .env.local && npm install && npm run dev
```

> Note: the Dockerfiles/compose config were written and YAML-validated
> in this environment, but **not build-tested with a real `docker`
> daemon** (unavailable in the sandbox this was built in). Everything
> they do was verified the long way instead — same Python versions,
> same `requirements.txt` pins, same `DATABASE_URL` patterns, same
> commands, run directly. Please run `docker compose up --build` once
> yourself before relying on it; if something's off it's almost
> certainly a path/context issue in a Dockerfile, not a logic error.

### Option B — Run everything directly (what was actually used to verify this scaffold)

```bash
# Postgres (adjust for your OS — this was verified against Postgres 16)
createdb campus_connect

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r db/requirements.txt -r requirements-dev.txt
pip install -r services/core-api/requirements.txt
export DATABASE_URL="postgresql+psycopg2://postgres:<pw>@localhost/campus_connect"
alembic upgrade head
python db/apply_grants.py   # run with a SUPERUSER DATABASE_URL, not a service role

# Then per service:
cd services/core-api && PYTHONPATH=.:../.. uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

## Regenerating placeholder icons

`scripts/gen_icons.py` (needs Pillow: `pip install pillow`) regenerates
every PWA/favicon icon from one simple glyph definition. Re-run it after
Phase 1 picks real branding, or just replace the PNGs under
`frontend/public/icons/` and `frontend/src/app/{icon,apple-icon}.png`
directly.

## Verification already done in Phase 0

Everything below was actually executed, not assumed:

- Frontend: `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build`
  all pass. Production server booted and `curl`-verified: manifest,
  service worker headers, icons, offline page, and the injected
  `<link rel="manifest">`/theme-color tags in real rendered HTML.
- Backend: all 5 services' health-check tests pass via `pytest`;
  `core-api` was also boot-tested for real with `uvicorn` and hit over
  HTTP. `ruff check` is clean across `db/` and all services.
- Database: migration generated via `alembic revision --autogenerate`
  against a live Postgres 16 instance, applied, and confirmed with
  `\dt`. Role isolation (`app_core_api` ⟂ `app_safety_service`, plus a
  column-level-restricted `app_safety_reviewer`) was proven by literally
  connecting as each role and confirming the expected `permission
  denied` errors — see the Phase 0 build log if you want the exact
  transcript.
- **Not verified**: `docker compose up` end-to-end (no Docker daemon in
  the build sandbox — see note above), and real browser PWA
  installability (no GUI browser available either). Both are
  server-side-correct as far as this environment can check; please
  confirm in your own environment before treating them as done-done.

## Known limitations (intentional, documented so they don't get "fixed" accidentally)

- **Service worker is hand-rolled, not Serwist.** It precaches a small
  stable shell (`/`, `/offline`, icons) and runtime-caches same-origin
  GETs as they're visited. A route the user never visited while online
  won't work on a cold offline load. Next.js's own PWA guide recommends
  Serwist for full precaching of hashed build output — worth revisiting
  in Phase 13/14 if full offline coverage becomes a real requirement.
- **No webfont.** `next/font/google` was removed because fetching
  Google Fonts at build time needs open egress that not every CI/deploy
  environment has (caught in the build sandbox itself). Phase 1 (design
  system) should make a deliberate typography call — prefer
  `next/font/local` with self-hosted files, or an npm-distributed font
  package, over a build-time external font CDN dependency.
- **`StarletteDeprecationWarning` in backend test output.** Current
  Starlette warns that `TestClient` will prefer a package called
  `httpx2` over `httpx` going forward. Non-blocking today (all tests
  pass), but worth watching — if a future `requirements.txt` bump drops
  `httpx` support in `TestClient`, swap the dev dependency then.
- **Dev-only passwords in `grants.sql`/`docker-compose.yml`.** Replace
  via real secrets management before any shared/staging/prod
  environment — never via committed `.env` files.

## Roadmap

See `Build_Prompt_Sequence.md` for the full phase-by-phase plan,
including **Phase 13 (Local Activity Discovery)** — a new feature (not
in the original R&D doc's 31 sections) for user-created, venue-based
real-world meetups with opt-in, coarse-location radius alerts. It's
sequenced after Phase 12 specifically because it depends on the
moderation/rate-limiting/reporting infrastructure that phase builds —
see that phase's entry for the full reasoning and safety constraints.

# Phase 14 launch gate — PWA hardening and deployment

Phase 14 supplies deployable artifacts and operational controls. It is not a
license to enable Phase 12 or 13: their separate live moderation/safety gates
remain mandatory and must be completed first.

## Before staging

1. Copy `deploy/.env.production.example` to the staging host as `.env`, set
   owner-only permissions, and replace every placeholder with staging-only
   secrets. Do not use Docker's development credentials or commit this file.
2. Put the frontend behind HTTPS and a reverse proxy that only exposes the
   frontend. Keep PostgreSQL and every service API on the internal Docker
   network. Configure the proxy with host allow-listing, request-size limits,
   rate limits, and `X-Forwarded-*` forwarding.
3. Create GitHub `staging` and `production` Environments. Each needs
   `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PATH`, `DEPLOY_SSH_PRIVATE_KEY`, and
   a pinned `DEPLOY_KNOWN_HOSTS`; production must require a reviewer. The
   server deploy path contains the production Compose file and its untracked
   `.env` file. Add the client-safe `NEXT_PUBLIC_CORE_API_URL` and
   `NEXT_PUBLIC_SAFETY_SERVICE_URL` Environment variables as well; they are
   baked into the frontend at build time, not read at container start.
4. Configure registry read access on the host. The release workflow publishes
   immutable SHA-tagged images and deploys only a selected tag. When a prior
   tag is supplied for rollback, it is only pulled and deployed—never rebuilt
   or overwritten.

## Required evidence

Record device/browser, app version, date, tester, and outcome for every item.

| Area | Required staging check |
|---|---|
| Installability | Install from Chrome/Edge on desktop and Android; on iOS Safari use Share → Add to Home Screen. Confirm name, 192/512 icon, maskable icon, splash colour, standalone launch, and update after a new deployment. |
| Offline/privacy | After opening the app online, turn on airplane mode. Confirm `/offline` is shown for a fresh protected navigation and static assets remain available. In browser storage tools, confirm no protected HTML, RSC, API response, check-in, journal, matching, room, or attendee data is in Cache Storage. Confirm check-in/tiny-action server mutations stay disabled and say they need reconnection. |
| Responsive/accessibility | Exercise actual small phone (320–390px), tablet (768px), and desktop (1280px+) devices or device emulators, with keyboard-only and 200% zoom. Check content is not obscured by the mobile navigation, buttons stay 44px-touch usable, and no horizontal overflow occurs. |
| Performance | Run a logged-in production-build Lighthouse audit on throttled mobile and desktop. Record scores, transfer size, largest JS bundles, and any remediation. Treat failures affecting task completion, accessibility, or low-bandwidth access as release blockers; retain raw reports rather than using a universal score threshold. |
| Rollout/rollback | Deploy an immutable tag to staging with the workflow, complete smoke tests, then promote that same tag to production. Re-run the workflow with the last known-good immutable tag to prove rollback. Confirm database migration compatibility before production; never roll a database backwards automatically. |

## Explicit offline contract

The PWA caches only the public offline page, icons, manifest, and immutable
Next build assets. It intentionally does **not** cache protected pages or
data: this is a wellbeing product and device cache is not an acceptable copy
of someone&rsquo;s journal/check-in/community data. A check-in or tiny action that
is already open remains readable and locally navigable; saving a check-in,
logging an action, or fetching a new suggestion requires connectivity and is
never silently queued.

## Deferred decision

Do not add Capacitor or a separate React Native app in this phase. Revisit
native distribution only after PWA usage and install evidence show a need for
app-store-specific capabilities.

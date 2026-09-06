# Phase-by-Phase Build Prompts
### For: Student Loneliness → Real-World Connection Platform
### Based on: `RnD_Student_Connection_Platform.md` (Sections 17–19 especially)

**Progress:** Phase 0 ✅, Phase 1 ✅ (see `frontend/DESIGN.md`), Phase 2 ✅, Phase 3 ✅, Phase 4 ✅ — Tiny Action Engine with the required repeated-failure safety signal, live-verified end-to-end (3 consecutive floor-reduced attempts across 3 different ladders correctly flipped the nudge from false→false→true on exactly the 3rd, through the real database and real Server Actions). A genuine bug was caught and fixed during this phase — see Phase 4's notes below. Next up: Phase 5 (Crisis/Safety System) — required before Phase 6 (Tiny Action Voice Layer) can make its first model call.

**Architecture pivot decided mid-build (see Phase 6 below, fully rewritten):** the original Phase 6 "AI Navigator" concept — an open-ended companion chatbot — has been replaced with something narrower and better-evidenced: a **Tiny Action Voice Layer**. The model's only job is phrasing one pre-selected tiny-action suggestion warmly; it never receives open text, never holds a conversation, and never claims to help with crisis content. This is deliberately a much smaller, safer surface than a companion chatbot — see Phase 6's full reasoning, including why it still waits for Phase 5 despite having no free-text attack surface. Model provider: the person building this is self-hosting their own trained weights (details TBD — inference server, format, and hosting still need to be specified); Gemini is being used as a prototyping stand-in as of this writing, and Phase 6 is written to keep the model backend swappable rather than hard-coding Gemini specifics throughout.

---

## Before you start: one architecture decision

"Runs on both mobile and desktop" has two real paths:

- **Path A — Responsive web app / PWA (recommended for this project).** One Next.js codebase, works in any browser, installable to a home screen/desktop as a Progressive Web App, no app-store review needed, fastest to iterate on. This is what the R&D doc's tech stack (Section 18) already assumes.
- **Path B — Native wrapper later.** Once the web app is solid, wrap it with Capacitor/Expo for real App Store/Play Store listings, if you decide you need push notifications at OS level or app-store presence.

**These phases build Path A first**, with Path B as an optional final phase. If you already know you want native from day one, say so before Phase 1 and I'll restructure the stack (React Native + a separate backend-consumption layer) instead — that's a different set of tradeoffs and best decided once, up front, not mid-build.

---

## How to use this

- **LLM provider constraint: Gemini API only.** The only API key available for this project is for Google's Gemini API — no OpenAI, no Anthropic. This affects Phase 5 (crisis classifier) and Phase 6 (AI Navigator) specifically; both phase prompts below already have this baked in. Every LLM call in this project goes through the Gemini API, called server-side only (from `core-api` or `safety-service`), never with the key exposed to the frontend.
- Paste one phase prompt at a time, in order. Each assumes the previous phases are done and working.
- Wait for me to finish and actually test/review the output before pasting the next one — don't queue them all at once. Small working slices are the point.
- Each prompt tells me which R&D doc section it's implementing, so I stay inside the evidence/safety constraints instead of improvising.
- Phases 0–2 are foundation, 3–7 are the P0 MVP (Section 17), 8–13 are P1, and 14 is launch readiness. Anything P2/P3 (Campus Map, ML matching, composite scores) is deliberately not in here — build and validate the MVP first.
- Swap in your own project name, campus name, and branding wherever you see `[PLACEHOLDER]`.

---

### Phase 0 — Project foundation & architecture scaffold

```
Set up the project foundation for [PLACEHOLDER APP NAME], a responsive web app (Next.js + TypeScript + Tailwind, installable as a PWA) that will run on both desktop and mobile browsers from one codebase.

Reference: RnD_Student_Connection_Platform.md, Section 18 (Technical Architecture) and Section 19 (Database Design).

Scope for this phase only:
1. Next.js (App Router) + TypeScript + Tailwind project scaffold.
2. Folder structure separating: UI components, feature modules, a `safety` module (kept isolated per Section 10/18 — this boundary matters, don't blur it later), and API/service layer.
3. FastAPI backend scaffold with the service boundaries from Section 18 (core-api, safety-service, matching-service, moderation-service, notification-service) — stub each as an empty but real service, not a monolith with folders pretending to be services.
4. PostgreSQL schema migration setup (e.g., Alembic) with the tables from Section 19, but only create the tables this MVP phase actually needs yet: users, profiles, checkins, tiny_actions, action_attempts, consent_records, privacy_settings, safety_events. Leave the rest as a documented "not yet" list in a schema-plan file so we don't forget them.
5. Basic CI (lint, type-check, test run) and a README explaining the architecture decisions and linking back to the R&D doc sections they implement.
6. PWA manifest + service worker scaffold (installable, works offline for at least the shell) — this is what makes "runs on mobile and desktop" true from one codebase.

Do not build any feature UI yet. This phase is infrastructure only. Confirm the dev server runs and the empty PWA installs before finishing.
```

---

### Phase 1 — Design system & responsive app shell

```
Build the design system and app shell for [PLACEHOLDER APP NAME].

Reference: Section 14 (UX Design / Information Architecture) — tone must be calm, human, non-clinical, non-judgmental; avoid hospital/medical dashboard aesthetics entirely.

Scope:
1. A Tailwind-based design system: color palette (warm, muted — no red/alarm colors as primary), typography scale, spacing, and a component library (buttons, cards, inputs, modals, bottom-sheet-on-mobile/side-panel-on-desktop pattern).
2. Responsive app shell: bottom tab navigation on mobile, sidebar navigation on desktop, from the same components (no separate mobile/desktop codepaths — one layout that adapts).
3. Placeholder routes/screens for: Home, Check-In, Tiny Action, Journal, Community, Professional Help, Safety Center, Settings — matching the information architecture in Section 14. Just empty states with correct navigation for now.
4. A persistent, unobtrusive "this is not therapy" disclosure pattern (small, always-visible footer or info affordance) — establish this convention now since every later AI-facing screen will reuse it.
5. Accessibility pass: color contrast, keyboard navigation, screen-reader labels on this shell.

No real feature logic yet — this is the shell everything else gets built inside.
```

---

### Phase 2 — Auth, onboarding, and consent architecture

```
Build authentication, onboarding, and the consent/privacy architecture for [PLACEHOLDER APP NAME].

Reference: Section 11 (Privacy Architecture), Section 19 (consent_records, privacy_settings, profiles tables).

Scope:
1. Auth integration (e.g., Clerk, or [YOUR CHOSEN PROVIDER]) with an optional pseudonymous display-identity mode that's decoupled from account identity, per Section 11.
2. Onboarding flow collecting only the minimum needed: no forced disclosure of mental-health history, no forced real name.
3. **Age handling is a hard gate, not a soft field**: implement whatever age-verification approach we agreed on (18+ only for MVP is the safer default per the R&D doc's India/DPDP discussion — confirm this with me before building if you haven't decided) and block onboarding completion until it's satisfied.
4. Granular, separately-toggleable consent screens (not one bundled "I agree"): AI chat use, anonymous community participation, matching/discovery visibility, any future institutional data sharing. Store each as its own row in `consent_records`.
5. A Privacy Center screen (from the Phase 1 shell) where a user can see and revoke each consent independently, and request data export/deletion (the deletion can be a stubbed admin-notify flow for now — full automated deletion pipeline can come later, but the request UI and record-keeping must exist now).

Do not build any AI or community feature yet. This phase is identity and consent only.
```

---

### Phase 3 — Check-In + "What do I need right now?" router ✅ done

> **As built:** the rules engine lives in `backend/services/core-api/app/checkin_rules.py` — a pure Python function, zero DB/network dependency, 27 unit tests covering every rule individually. Business logic lives in `core-api` (not the Next.js layer) to stay consistent with Phase 2's pattern — the frontend's Server Action is a thin orchestrator, not a second copy of the routing logic. Crisis-resource visibility (scope item 5) is satisfied by Phase 1's existing `SafetyDisclosure` component, already persistent on every `(app)` screen — no separate crisis button was needed. Live-verified end-to-end: a real submission of feelings=[lonely, exhausted] + need=relax + time=night correctly triggered the "lonely at night" presence-mode modifier specifically, not a generic fallback.

```
Build the 60-Second Check-In and the rules-based need router.

Reference: Section 5.1 and 5.2 of the R&D doc (or the "60-Second Emotional Check-In" and "AI Need Engine" features), Section 20 (Recommendation Engine — rules-first, not ML, at this stage).

Scope:
1. Check-in UI: quick-select feeling chips (lonely, sad, anxious, overwhelmed, angry, empty, exhausted, unmotivated, confused, "don't know") — no free-text required, no scoring, no percentage output.
2. "What do you need right now?" follow-up: talk / distraction / understand my feeling / get motivated / be around people / study / relax / ask for help.
3. A **deterministic rules engine** (not an LLM call) mapping feeling + need + time-of-day to a suggested path (tiny action / presence mode placeholder / professional help placeholder / crisis resources always-visible). Write this as a plain, readable rules table in code, not a black box — we need to be able to audit and edit it directly.
4. Store check-ins per the `checkins` table (feelings array + stated need, no free text unless explicitly opted in later).
5. The crisis-resources link/button must be visible on this screen and every screen downstream of it regardless of what the rules engine picks — never gate it behind a "wrong" routing decision.

No AI/LLM calls in this phase — everything is deterministic. That's intentional per Section 10.
```

---

### Phase 4 — Tiny Action Engine (core loop) ✅ done

> **As built:** 10 ladders seeded (3 per social/study, 2 per movement/rest), 30 rows total, each with real written copy — not lorem ipsum. `ladder_parent_id` points toward the *harder* neighbor (hardest rung = ladder root); the default entry point is always the middle rung, giving room to go either direction. The suggestion endpoint deliberately picks a random ladder rather than smart-matching to the triggering check-in's category — a stated scope line, not a silent gap (need→category mapping has real ambiguity, e.g. what fits "get_motivated"?). `checkinId` is threaded from Check-in through a URL param specifically so `action_attempts.related_checkin_id` is genuinely populated, not just schema-ready.
>
> **A real bug was caught and fixed here, not just theorized about.** The repeated-failure query initially counted the automatic `SUGGESTED` attempts (logged every time a fresh suggestion is fetched) alongside the `REDUCED` ones — which meant in the *actual* UI flow (fetch suggestion → reduce → fetch new suggestion → reduce...), the `SUGGESTED` rows interleaved between the `REDUCED` rows and silently prevented the safety signal from ever firing. A test that called the reduce endpoint in isolation wouldn't have caught this — it only surfaced because the test simulated the real interaction pattern. Fixed by excluding `SUGGESTED` from the pattern query; a regression test now pins the exact bug. Live-verified afterward: 3 consecutive floor-reduces across 3 different ladders correctly went false → false → true.

```
Build the Tiny Action Engine — the structural core of the product per Section 5.3 / Section 29 (Final Product Concept) of the R&D doc.

Scope:
1. A content model for tiny actions with explicit difficulty ladders (e.g., "message one classmate" → "go where people are" → "step outside for 2 minutes"), stored per the `tiny_actions` table (category, difficulty_level, ladder_parent_id).
2. Seed a real starter library of actions across categories (social, study, movement, rest) with at least 3 ladder rungs each — write these yourself in a warm, non-patronizing tone, don't leave them as lorem ipsum.
3. UI: today's suggested action, a "make it smaller" control that steps down the ladder, a "make it bigger" control that steps up, complete/skip/reduce buttons.
4. `action_attempts` logging (suggested/attempted/completed/reduced) tied to the check-in that triggered it where applicable.
5. A **repeated-failure signal**: if a user hits "couldn't do it" at the easiest rung of a ladder multiple times in a row, surface (don't force) a suggestion to look at Professional Help or Crisis resources — this is a required safety behavior per Section 5.3, not optional polish.
6. No streaks, no "you failed today" language anywhere — reference Section 15 (Gamification) for the tone constraint: consistency shown without penalty framing.

This is the feature most of the rest of the app should end up feeding into — build it solid.
```

---

### Phase 5 — Crisis / Safety System (build before any AI feature)

```
Build the Crisis / Safety System. This must exist and pass review before Phase 6 (AI Navigator) starts — do not build the AI companion first and bolt this on after.

Reference: Section 10 (AI Architecture — layered safety design), Section 5.14 / Section 14-G (Crisis flow), Section 19 (safety_events table, most access-restricted table in the schema).

Scope:
1. A standalone, independently-callable crisis-language classifier service (`safety-service`) that any text-input feature (check-in free text if ever added, AI chat, community posts) must pass through BEFORE that text reaches any LLM or is stored/displayed. **Given the Gemini-only constraint, this will call the Gemini API itself** — but as a narrow, constrained-output classification call, not open conversation: force a strict structured output (e.g., a flag level and nothing else — no free-text reasoning returned to the caller), keep the prompt focused only on detecting crisis-indicative language, and bias the threshold toward over-flagging rather than under-flagging. Be honest in code comments that this is a **weaker mitigation than a dedicated, purpose-trained safety classifier** (general LLMs have documented ~20% unsafe-response rates in crisis scenarios per published research) — this is what's achievable with the available API access now, and should be revisited if/when a dedicated classifier model or vendor becomes available. Do not present this to me or in any user-facing copy as more rigorously validated than it is.
2. A deterministic (not LLM-generated) supportive response script shown immediately on a flag — calm, validating, non-interrogative language you write and I can review, not invented at runtime. This step stays deterministic regardless of provider — the classifier's job is only to flag, never to compose the response shown to the student.
3. Always-visible crisis resource display: [YOUR REGION'S HELPLINES — e.g., for India: Tele-MANAS 14416/1-800-891-4416, KIRAN 1800-599-0019, Vandrevala Foundation 1860-266-2345]. Make this list a config file, not hardcoded, so it can be updated without a redeploy and swapped per region later.
4. `safety_events` logging with the most restrictive access control in the whole schema — a separate role/permission, not just "admin can see everything." Log the classifier's flag level and the Gemini model/prompt-version used, so a future swap to a different provider or a dedicated classifier is auditable against past behavior.
5. Explicitly do NOT build: any auto-contact of trusted persons/parents, any diagnostic language, any promise of confidentiality we can't guarantee. Write a short in-code comment block citing Section 10/14 next to this logic so future contributors don't "fix" it into something less safe.
6. A minimal internal review screen where a human (you, for now) can see flagged events and their outcomes — this is the seed of the human-escalation layer from Section 10. Given point 1's honest limitation, treat a higher-than-ideal false-positive rate from this review screen as expected and acceptable — false positives are the safe failure mode here, false negatives are not.

Test this phase with a written test set of both true crisis language and adjacent-but-not-crisis language (e.g., "this exam is killing me") to check for both misses and over-triggering, and show me the results before we move on — pay particular attention to any misses, since that's the failure mode that matters most.
```

---

### Phase 6 — Tiny Action Voice Layer (narrow, scoped, gated by the safety layer)

> **Rewritten from the original "AI Navigator" concept.** The original plan was an open-ended companion chatbot. That's been replaced — this phase now does one job only: phrase an already-selected Tiny Action suggestion warmly. It has no conversation, no memory across turns, and never receives open user text. This is a deliberately much narrower, better-evidenced surface — see Section 5's Feature 3 (Tiny Action Engine) evidence rating vs. Feature 13's (AI Companion) risk rating in the R&D doc.

```
Build the Tiny Action Voice Layer: takes ONE already-selected tiny action (from Phase 4's logic) plus structured check-in tags, and generates ONE short, warm message presenting it. This is NOT a chatbot — no back-and-forth, no free-text input, no memory.

Reference: this replaces the original Section 5.13/Section 10 "AI Navigator" concept with something narrower. Keep everything from Section 10 that still applies (server-side only, never expose the key to the frontend, log model/prompt-version per call) — drop everything that assumed open conversation (memory across turns, reflective back-and-forth, "help identify immediate needs" through dialogue).

Why this still waits for Phase 5, even with no free-text input: this feature's input is fully structured (feeling tags, a need tag, the action's title, difficulty level, time of day) — Phase 3's check-in is quick-select only, no free text — so there is genuinely no direct path for crisis language to reach this model the way there would be for an open chatbot. That's a real, narrower risk profile, and worth being honest about rather than pretending this is exactly as risky as the original AI Navigator. But it still ships after Phase 5, for two concrete reasons, not just "better safe than sorry": (1) Phase 4's own design calls for repeated tiny-action failures to surface Professional Help/Crisis resources — that routing is better served with Phase 5's resource-display config already built and proven; (2) keeping "no AI-generated user-facing text ships before the safety foundation exists" exception-free is worth more than the time saved by carving out this one exception now — that kind of case-by-case exception is exactly how safety discipline erodes on a real project.

Scope:
1. Define a small, provider-agnostic interface for this — something like `generateTinyActionMessage(input): Promise<string>` — where `input` is `{ feelings: string[], statedNeed: string, actionTitle: string, difficultyLevel: number, timeOfDay: string }`. Implement it once against Gemini (the current prototyping backend) behind this interface, NOT scattered Gemini-specific calls throughout the codebase — the person building this intends to swap in their own self-hosted model later (weights/inference server TBD), and that swap should mean writing one new implementation of this interface, not a rewrite.
2. The system prompt (already drafted and tested in a Colab prototype — reuse it, don't redrive from scratch) enforces: 1–3 sentences max, plain warm language, references the specific feeling/need tags given, frames the action as optional ("if you're up for it," never a command), never claims to fix/cure/solve anything, never asks a follow-up question, and has an explicit hard-stop refusal if crisis-adjacent content somehow appears in the input (defense in depth, even though Phase 3 shouldn't produce free text that could contain it).
3. A deterministic rule-adherence safety net wrapping every call: reject and regenerate (once) if the output contains a `?`, exceeds ~3 sentences, or exceeds a length cap; if it still fails after one retry, fall back to a plain, pre-written static message rather than surfacing a rule-breaking output. This net should already exist from the Colab prototyping — port it in, don't rebuild it from scratch.
4. Server-side only, called from `core-api` (or wherever Phase 4's tiny-action logic lives) — the API key/inference-server address is an environment variable, never sent to the frontend, never in a `NEXT_PUBLIC_*` var.
5. Handle failures/timeouts gracefully and visibly: if the model call fails entirely, fall back to Phase 4's own static tiny-action description (which already exists as the `title`/`description` content) rather than blocking the suggestion from appearing at all — a slower or failed model call should never mean the student sees nothing.
6. Log the model/prompt-version used per call (same auditability reasoning as Phase 5), so a future swap between Gemini and the self-hosted model is comparable against past behavior.
7. UI: this generated message replaces/enhances Phase 4's static suggestion text — it does not introduce a new screen or a chat-style interface. The Phase 1 "not therapy" disclosure convention still applies wherever this message is shown.

Explicitly NOT in scope for this phase (these would be the actual "AI Navigator" from the original plan, and are not currently planned): open-ended conversation, multi-turn memory, "ask reflective questions," message-drafting help for the student's own messages to others. If an open-ended companion is wanted later, that's a new, separate, much higher-risk feature requiring its own dedicated safety review — not an extension of this one.

Test this with the same kind of adversarial input set Phase 5 uses (varied feelings/needs/difficulty/time combinations) and show me a batch of real generated outputs against the 8 rules before this ships, plus at least one forced-failure test (simulate the model timing out or erroring) to confirm the static fallback actually fires.
```

---

### Phase 7 — Professional Help Navigation

```
Build the Professional Help Navigation feature.

Reference: Section 5.16, Section 3 (L–M barriers to help-seeking — this is the best-evidenced, highest-leverage feature in the doc, treat it with real care not as an afterthought).

Scope:
1. A human-curated, versioned resource directory (retrieved from a data table, never LLM-generated) covering: what campus/local counseling looks like, how to book a first session, what to expect, and a directory of verified resources for [YOUR REGION].
2. "What to say" script content — example opening lines for a first counseling conversation, written to reduce fear specifically (per the barriers evidence), not to persuade/convince.
3. This section must be reachable directly from the home screen without requiring a check-in first — a student in distress should never be routed through an unrelated flow to reach this.
4. Admin/editor interface (even a simple one) for updating the resource directory without a code deploy, since contact details and hours change.

No AI generation of resource content in this phase — retrieval only, per Section 10's constraint on high-stakes information.
```

---

### Phase 8 — Progress Journal & Real-Life indicators

```
Build the Future-Self Journal and the (non-composite) Real-Life behavior log.

Reference: Section 5.11, 5.12 — explicitly avoid any single "score" or percentage.

Scope:
1. Private-by-default journal (encrypted at rest) with simple entry/timestamp storage, and a "what changed" view comparing entries across 7/30/90-day windows as narrative text, not a chart with a number.
2. A small set of separate, human-readable behavioral indicators (tiny actions completed, activities joined once that feature exists, help-seeking actions taken) shown as plain counts/short sentences — never combined into one aggregate score.
3. Export/delete controls for journal data specifically, wired into the Privacy Center from Phase 2.

This phase has no AI dependency and can be built independently of Phase 6 if you want to parallelize.
```

---

### Phase 9 — Activity-Based Connection & Presence Mode

```
Build Activity-Based Connection and Presence Mode (P1 features).

Reference: Section 5.6, 5.7 — Presence Mode should be framed to users honestly as "many students find this helps them feel less alone while working," not as a clinically proven feature (Section 5.7's evidence rating is early/limited, be honest about it in copy).

Scope:
1. Activity rooms (study/coding/reading/etc.) with scheduled or ad-hoc join, real-time presence via WebSockets, anonymized headcounts only.
2. Presence Mode: camera/audio optional and off by default, zero interaction required, one-tap join/leave, light optional post-session "how did that feel" prompt (skippable).
3. `presence_rooms` and `activities` tables per Section 19.
4. No individual location data anywhere in this feature — rooms are virtual/topic-based at this stage, not tied to physical campus locations yet (that's the P2 Campus Map, out of scope here).

Rate-limit room creation/joining to prevent spam before this ships to real users.
```

---

### Phase 10 — Trusted Person System

```
Build the Trusted Person System.

Reference: Section 5.15 — explicit design constraint: never auto-contact anyone.

Scope:
1. Let a student optionally add trusted contacts (friend, parent, sibling, teacher, counselor, mentor — no default assumption that family is the safe choice).
2. Encrypted storage of contact info, per-scenario consent scope flags (not a blanket "contact them if X").
3. A one-tap "reach out to my trusted person" flow that the student initiates themselves — this only ever sends when the student explicitly taps it, never automatically based on usage patterns, mood trends, or inactivity.
4. Surface this option (never forced) from the crisis flow in Phase 5, as an alternative alongside professional resources.

Explicitly do not build any automatic notification to trusted contacts based on app behavior — this is a hard line from Section 15/28 of the R&D doc.
```

---

### Phase 11 — Matching ("Find Someone Like Me")

```
Build the Find Someone Like Me matching feature.

Reference: Section 5.5, Section 21 (Matching Algorithm) — explicitly non-dating.

Scope:
1. Rules-based matching on interests/course/year/activity type (from `user_interests`), no photo-first UI, no romantic/appearance-based signals anywhere in the data model or UI copy.
2. Block-list and report-history exclusion baked into the matching query itself, not just a UI filter.
3. A specific report category for "used this for dating/romantic approach" in the reporting flow.
4. Region/language matching (if you want it for homesickness use cases) must be a backend weighting signal only — never a publicly browsable filter ("students from X region") per the privacy risk flagged in Section 4/24.

This can ship without Anonymous Rooms (Phase 12) — they don't depend on each other.
```

---

### Phase 12 — Anonymous Situation Rooms + Moderation (gate this carefully)

```
Build Anonymous Situation Rooms — but only after confirming the moderation pipeline described below is genuinely working, per Section 5.4's explicit gate ("do not ship without moderation infrastructure live").

Reference: Section 5.4, Section 22 (Moderation System), Section 12 (Threat Model).

Scope:
1. Situation-based (not diagnosis-based) room topics: feeling lonely, exam anxiety, homesick, need someone to talk to, etc.
2. Automated content classifiers running on every post before or immediately after posting: toxicity/harassment, self-harm content, sexual content, spam/scam patterns. Route the self-harm classifier through the same safety-service from Phase 5, don't build a second, inconsistent one.
3. Human moderator review queue for anything flagged or borderline, with role-based access separate from general admin.
4. Rate limiting on new/anonymous accounts specifically.
5. Community guidelines and reporting tools shown before a user can post, not buried in settings.
6. Crisis resources persistently visible inside every room, not just triggered by a flagged post.

Load-test the moderation queue with a simulated burst of flagged content before considering this launch-ready. If the moderation pipeline isn't solid, tell me — we hold this feature back rather than ship it half-safe, per the R&D doc's own instruction.
```

---

### Phase 13 — Local Activity Discovery (new feature, added after initial planning)

> **Not in the original R&D doc's 31 sections** — added by request partway through the build. It's placed here, after Phase 12, on purpose: see "Why here" below before moving it earlier.

```
Build Local Activity Discovery: user-created, real-world venue-based activities (cricket, football, study groups, coding sessions, coffee chats, walks, gym sessions, etc.) that nearby students can discover and join — distinct from Phase 9's virtual/topic activity rooms.

Reference: this extends R&D doc Section 5.6 (Activity-Based Connection) into user-generated real-world events, and implements the PRIVACY-SAFE intent of Section 5.8 (Campus Social Map) using opt-in user-created events instead of ambient location aggregation — see "Relationship to Campus Map" below. Inherits its safety posture from Section 11 (Privacy Architecture) and Section 22 (Moderation System), and reuses the moderation/rate-limiting infrastructure Phase 12 just built.

Scope:
1. Activity creation: title, description, category, PUBLIC VENUE ONLY, date & time, max participants. Venue must be selected from a places/business lookup (e.g., a places-search API), never a freeform address field — this is how "no residential addresses" gets enforced technically, not just stated as a rule in copy. Reject creation if no valid public venue is selected.
2. Join / Maybe / Ignore RSVP states per activity, with participant COUNTS shown — never a participant list with exact identities exposed beyond what the student's own privacy settings (Phase 2) already allow, consistent with the pseudonymous-identity architecture from Phase 2.
3. Opt-in radius discovery: a student may optionally share a COARSE area (not exact location) to see nearby activities and receive alerts. Coarse-grain this server-side by snapping to a geohash cell (or similar fixed-precision grid) at a precision that corresponds to roughly neighborhood/city-district size, not by trusting a client-supplied "approximate" value — the server must be the one enforcing the imprecision, since a client-side-only approximation can be bypassed or misconfigured.
4. On activity creation, notify opted-in users within the configurable radius whose profile interests (from `profiles.interests`, already in the schema since Phase 0) overlap the activity's category — this is core-api calling notification-service, not a cross-service DB join.
5. Add a new `consent_records` type: `activity_alerts` (additive enum migration — see docs/schema-plan.md). No student receives radius-based notifications without this consent explicitly granted, separately from every other consent type.
6. Reuse Phase 12's moderation pipeline for activity titles/descriptions (spam, scam, harassment, predatory-pattern detection) and its reporting flow — do not build a second, inconsistent moderation system for this feature.
7. Rate-limit activity creation per user/account age more aggressively than Phase 12's anonymous-room rate limits — an in-person meetup invitation reaching many nearby strangers is a materially higher physical-safety stakes action than an anonymous text post, and the rate limiting should reflect that (e.g., a new/unverified account should not be able to immediately blast a wide-radius activity to a large notified audience).
8. Mobile-first responsive activity cards + a venue display (map pin ON THE VENUE only, never on any individual user, never showing distance between two students) + notification delivery via notification-service.

Hard safety requirements (do not treat these as configurable/optional):
- NEVER store or expose exact user coordinates, only the server-coarsened area cell described in item 3.
- NEVER compute or display distance between two individual users — only "this activity is happening in your area," never "this student is 800m from you."
- Only the activity's public venue is ever shown on a map — no individual is ever a map pin.
- Venue must be a verified public place (item 1's enforcement), never a residential address or live/real-time location share.
- Everything in this list is a stricter, real-world-consequence version of the location-privacy constraints already established for the (deferred, P2) Campus Map feature in Section 5.8/12 — do not loosen them because this feature ships first.

New tables (see docs/schema-plan.md): `activity_meetups`, `activity_rsvps`, `activity_alert_preferences`. Relate to, but do not merge with, Phase 9's `activities`/`presence_rooms` tables — those are virtual/topic rooms; these are real-world venue events with a creator, an RSVP model, and a notification fan-out, which is meaningfully different data shape and risk profile.

Why here (after Phase 12, not earlier): this feature hard-depends on the moderation/rate-limiting/reporting infrastructure Phase 12 builds — user-generated content that can lead to an in-person meetup is at least as abuse-prone as anonymous text rooms, arguably more so given the physical-safety dimension, so it should not ship with less moderation maturity than Phase 12 required for itself. It does not require Phase 11 (Matching) to precede it — the interest-overlap check in item 4 only needs `profiles.interests`, which exists from Phase 0.

Relationship to Campus Map (Section 5.8, still P2/deferred): this feature and Campus Map are different mechanisms — this one is active/opt-in/user-created events, Campus Map was passive ambient-headcount aggregation per pre-defined campus location. Shipping this feature does NOT by itself validate or unblock Campus Map; that still needs its own usage-data justification per Section 17's original gate. Don't build Campus Map next just because this shipped.

Load-test the notification fan-out and re-confirm the moderation pipeline handles this feature's content types (venue/title/description spam, predatory-meetup-pattern language) before this goes live — the Phase 12 load test covered anonymous room posts, not this feature's specific content shapes.
```

---

### Phase 14 — PWA hardening, offline behavior, and deployment

```
Finish the "runs on mobile and desktop" requirement properly and prepare for deployment.

Scope:
1. Full PWA audit: installable on iOS/Android/desktop Chrome/Edge, correct icons/splash screens, offline fallback for at least the shell and previously-loaded content (check-in and tiny-action screens should work offline-first where possible, given this is exactly when a student might need them — e.g., poor hostel wifi, per Section 25's accessibility notes).
2. Responsive QA pass across real breakpoints (small phone, tablet, desktop) — not just resizing a desktop browser window.
3. Performance pass: Lighthouse scores, bundle size, especially for low-bandwidth contexts (Section 25 flags this as a real accessibility constraint, not a nice-to-have).
4. Deployment pipeline (staging + production) for frontend and backend, with environment-separated secrets and a rollback plan.
5. If/when you want real native app-store presence later, this is the point to evaluate Capacitor (wraps this same PWA) vs. a separate React Native build — flag this as a future decision, don't build it now unless you tell me you need it.

This phase makes the app genuinely usable on both device classes, not just theoretically responsive.
```

---

## Suggested order recap

| Phase | What | MVP tier |
|---|---|---|
| 0 | Architecture scaffold | Foundation |
| 1 | Design system & responsive shell | Foundation |
| 2 | Auth, onboarding, consent | Foundation |
| 3 | Check-in + need router | P0 |
| 4 | Tiny Action Engine | P0 |
| 5 | Crisis/Safety System | P0 — before any AI |
| 6 | Tiny Action Voice Layer *(rewritten — was "AI Navigator")* | P0 |
| 7 | Professional Help Navigation | P0 |
| 8 | Journal & indicators | P1 |
| 9 | Activity Connection & Presence Mode | P1 |
| 10 | Trusted Person System | P1 |
| 11 | Matching | P1 |
| 12 | Anonymous Rooms + Moderation | P1, gated |
| 13 | Local Activity Discovery *(new)* | P1, gated on Phase 12 |
| 14 | PWA hardening & deployment | Launch readiness |

Not included on purpose (P2/P3 per Section 17 of the R&D doc — revisit only after the MVP is validated with real students): Campus Social Map — see Phase 13's "Relationship to Campus Map" note, it stays deferred even after Phase 13 ships — Loneliness Pattern Discovery, composite connection scoring, ML-based matching, automated trusted-contact escalation.

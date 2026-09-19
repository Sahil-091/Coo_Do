# Schema plan — deferred tables

Phases 0–13 create only the tables the P0 MVP needs (see root README and
R&D doc Section 19): `users`, `profiles`, `checkins`, `tiny_actions`,
`action_attempts`, `tiny_action_voice_events`, `consent_records`,
`privacy_settings`, `safety_events`, `professional_resources`, `journal_entries`,
and `help_seeking_actions`, plus the Phase 9 virtual-only `activities`,
`presence_rooms`, and private `activity_participants` tables.
It also includes the Phase 10 `trusted_contacts` table, whose identifying and
destination data are encrypted at rest, Phase 11's matching tables, and
Phase 12's anonymous-room moderation tables.

The Phase 11–13 rows below are implemented. Phase 12 and Phase 13 retain
their documented external staging/staffing launch gates; implementation does
not mean launch-ready. Phase 14 adds no database tables, but its PWA and
deployment artifacts have a separate device/browser and rollout evidence gate.
"Owner service" follows the boundary in R&D doc
Section 18/21 — cross-service DB access should never happen; a service
that needs data from another owns a call to that service's API, not a
join into its tables.

`tiny_action_voice_events` is a Phase 6 core-api metadata-only audit table.
It records provider/model/prompt version, call attempt, and outcome for each
model invocation; it deliberately does not duplicate check-in tags or model
prose. Phase 6 also stores the fixed `time_of_day` tag on `checkins`, because
it is part of the structured input that the bounded voice call receives.

| Table(s) | Added in | Owner service | Notes |
|---|---|---|---|
| `matches`, `match_blocks`, `match_reports` | Phase 11 | matching-service | Compatibility/match state plus SQL-enforced bilateral block/report exclusions. `dating_or_romantic_approach` is an explicit report category. Reads selected `profiles` signals from core-api via API, not a cross-service join. |
| `community_rooms`, `community_posts`, `community_reports`, `moderation_events` | Phase 12 | moderation-service | Fixed situation topics; every post is screened before public display, flags/reports enter a role-separated review queue, and young accounts have tighter post/room limits. Not launch-ready until the live load-test gate passes. |
| `activity_meetups`, `activity_rsvps`, `activity_alert_preferences` | **Phase 13 (new — Local Activity Discovery, code-complete; launch gate pending)** | core-api (creation/RSVP and local recipient filter) + notification-service (handoff/fan-out) + moderation-service (shared pre-publication screening) | Real-world, venue-based, user-created events — distinct from Phase 9's virtual activity rooms. `activity_alert_preferences` contains only a server-generated coarse cell, never coordinates. API responses contain RSVP counts and the caller's own state only—never attendee identities. See `docs/phase-13-launch-gate.md` for required live evidence. |
| `campus_locations` | **P2 — not in the current phase plan** | — | Original R&D doc Feature 8 (ambient per-location headcounts, e.g. "12 students studying in the library"). This is a *different* mechanism from Phase 13 (passive aggregation vs. active user-created events) and stays gated behind real usage data justifying it, per R&D doc Section 17 — Phase 13 shipping does not by itself unblock this. |

## Consent/privacy model additions still needed

`consent_records.consent_type` includes the additive `activity_alerts` value
introduced by Phase 13. It is distinct from merely enabling an area: both a
currently granted consent record and an enabled coarse-area preference are
required before core-api hands an alert to notification-service.

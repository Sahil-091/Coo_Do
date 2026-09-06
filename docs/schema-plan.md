# Schema plan — deferred tables

Phase 0 creates only the tables the P0 MVP needs (see root README and
R&D doc Section 19): `users`, `profiles`, `checkins`, `tiny_actions`,
`action_attempts`, `consent_records`, `privacy_settings`, `safety_events`.

Everything below is intentionally **not yet built**. Listed so nothing
gets silently forgotten. "Owner service" follows the boundary in R&D doc
Section 18/21 — cross-service DB access should never happen; a service
that needs data from another owns a call to that service's API, not a
join into its tables.

| Table(s) | Added in | Owner service | Notes |
|---|---|---|---|
| `professional_resources` | Phase 7 | core-api | Human-curated, versioned directory — retrieval only, never LLM-generated (R&D doc Section 10, 16). |
| `journals` | Phase 8 | core-api | Private-by-default, narrative-first. No composite scoring, ever (Section 5.11–12). |
| `activities`, `activity_participants`, `presence_rooms` | Phase 9 | core-api (or a future dedicated `activity-service` if load justifies splitting it out) | Virtual/topic-based rooms (study, coding, reading) + zero-interaction Presence Mode. **Not** the real-world venue events below — see Phase 13. |
| `trusted_contacts` | Phase 10 | core-api | Encrypted contact info, per-scenario consent scope. Never auto-contacted (Section 15, 28). |
| `matches` | Phase 11 | matching-service | Compatibility/match state (pending/accepted/declined/blocked). Reads `profiles.interests` from core-api's tables via API call, not a cross-service join. |
| `communities`/`rooms`, `messages`, `reports`, `moderation_events` | Phase 12 | moderation-service | Gated: do not build ahead of the moderation pipeline being load-tested (Section 5.4, 22). |
| `activity_meetups`, `activity_rsvps`, `activity_alert_preferences` | **Phase 13 (new — Local Activity Discovery)** | core-api (creation/RSVP) + notification-service (radius fan-out) + moderation-service (reporting/rate-limiting, reused from Phase 12) | Real-world, venue-based, user-created events — distinct from Phase 9's virtual activity rooms. See `Build_Prompt_Sequence.md` Phase 13 for the full spec and safety constraints (coarse-location-only, no exact coordinates, no inter-user distance, public-venue enforcement). |
| `campus_locations` | **P2 — not in the current phase plan** | — | Original R&D doc Feature 8 (ambient per-location headcounts, e.g. "12 students studying in the library"). This is a *different* mechanism from Phase 13 (passive aggregation vs. active user-created events) and stays gated behind real usage data justifying it, per R&D doc Section 17 — Phase 13 shipping does not by itself unblock this. |

## Consent/privacy model additions still needed

`consent_records.consent_type` (Phase 0 enum: `ai_chat`,
`anonymous_community`, `matching_visibility`,
`institutional_data_sharing`) will need a new value —
`activity_alerts` — added in Phase 13 for the opt-in radius-notification
feature. This is an additive enum migration, not a breaking one.

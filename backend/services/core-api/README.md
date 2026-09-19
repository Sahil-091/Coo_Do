# core-api

Owns users, profiles, checkins, tiny_actions, action_attempts,
tiny_action_voice_events, consent_records, privacy_settings. The main
app-facing API.

Phase 13 additionally owns public-venue meetup creation, coarse-area
preferences, RSVP counts, and the recipient eligibility filter. Exact user
coordinates are converted immediately to a broad area cell and are neither
stored nor returned. `notification-service` receives only recipient IDs that
already satisfy active `activity_alerts` consent, enabled cell, and
profile-category overlap; it does not query core-api tables.

Phase 10 trusted-contact names and SMS/email destinations use a separate,
required `TRUSTED_CONTACT_ENCRYPTION_KEYS` Fernet keyring. The service only
returns an SMS/email composer URI after an explicit student action; it has no
automatic-contact route or background notification job.

Phase 6's Tiny Action Voice Layer is a bounded Gemini adapter behind
`app.tiny_action_voice.TinyActionVoiceProvider`. It receives only a stored,
enum-backed check-in plus one curated action; it is not a chat endpoint and
never accepts browser text. Invalid, refused, timed-out, or unavailable model
output falls back to the Phase 4 static action description. `GEMINI_API_KEY`
and `GEMINI_MODEL` belong only in core-api's server environment.

After configuring a real Gemini key, run the opt-in batch review with
`PYTHONPATH=backend:backend/services/core-api GEMINI_API_KEY=... python
scripts/run_live_tiny_action_voice_evaluation.py` (use `;` instead of `:` in
PowerShell). It prints real model outputs and their deterministic guard result;
it does not run in CI or with a missing key.

Independently runnable FastAPI service — has its own `requirements.txt`
and `Dockerfile` so it can be deployed on its own, per R&D doc Section 18
(service boundaries) and Section 21.

## Run locally
```
cd backend/services/core-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port <see docker-compose.yml>
```

# notification-service

Owns opt-in, non-manipulative notification delivery per Section 19. Phase 13
adds an authenticated activity-alert handoff. Core-api calculates recipients
from its own consent, coarse-cell, and interest data, then sends only recipient
IDs, meetup ID, and category here—never coordinates, area cells, profiles, or
attendee identities. A production delivery adapter and its staged load evidence
remain required by `docs/phase-13-launch-gate.md` before these alerts launch.

Independently runnable FastAPI service — has its own `requirements.txt`
and `Dockerfile` so it can be deployed on its own, per R&D doc Section 18
(service boundaries) and Section 21.

## Run locally
```
cd backend/services/notification-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port <see docker-compose.yml>
```

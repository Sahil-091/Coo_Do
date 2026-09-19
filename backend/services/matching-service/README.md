# matching-service

Owns Phase 11's rules-based, explicitly non-dating matching state. It asks
core-api for an age-verified, consented and matching-visible candidate pool;
it cannot read core-api tables directly. Before ranking candidates, the
matching SQL query applies bilateral `match_blocks` and `match_reports`
exclusions using `NOT EXISTS`. Region/language are private tie-breakers only,
never returned as browseable filters.

Independently runnable FastAPI service — has its own `requirements.txt`
and `Dockerfile` so it can be deployed on its own, per R&D doc Section 18
(service boundaries) and Section 21.

## Run locally
```
cd backend/services/matching-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port <see docker-compose.yml>
```

# moderation-service

Owns Phase 12's anonymous situation rooms, pre-publication moderation, member
reports, and the human-review queue. Every post is screened through
safety-service for self-harm language before storage/display, then through
deterministic toxicity/harassment, sexual-content, and spam/scam classifiers.
Any flag is held from the room and queued for a separately credentialed
moderator. Posts fail closed when the canonical safety screen is unavailable.

The separately role-gated reviewer UI is `/community/review`; it uses a
different reviewer token and email allow-list from the crisis safety queue.

This is **not launch-ready until** `scripts/load_test_moderation_queue.py`
has been run against a real deployed stack and the staffed-review process has
been confirmed. The queue should never be bypassed to ship rooms sooner. The
exact evidence and staging-only procedure are in
[`docs/phase-12-launch-gate.md`](../../../docs/phase-12-launch-gate.md).

Independently runnable FastAPI service — has its own `requirements.txt`
and `Dockerfile` so it can be deployed on its own, per R&D doc Section 18
(service boundaries) and Section 21.

## Run locally
```
cd backend/services/moderation-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port <see docker-compose.yml>
```

# safety-service

Owns safety_events exclusively. Independently deployable per R&D doc Section 21, so a safety-classifier update never requires redeploying the rest of the stack.

## Phase 5 safety boundary

`POST /v1/check-text` is internal-only and must be called before any text is
sent to an LLM, stored, or shown publicly. It asks Gemini for a constrained JSON
flag only (`none`, `elevated`, or `crisis`). Gemini's result never supplies user
copy: `app/support_scripts.py` contains the only deterministic message that can
be returned on a flag.

This is not a dedicated, clinically validated safety classifier. General-purpose
LLMs are a weaker mitigation and may miss crisis language, so provider failures
return 503 and callers must stop downstream work and display resources.

The region resource file is read on every request. Set `SAFETY_RESOURCES_FILE`
to an operator-managed mounted file to update helplines without rebuilding this
service. Run the opt-in Gemini regression check with:

```bash
PYTHONPATH=../.. GEMINI_API_KEY=... python scripts/run_live_safety_evaluation.py
```

Independently runnable FastAPI service — has its own `requirements.txt`
and `Dockerfile` so it can be deployed on its own, per R&D doc Section 18
(service boundaries) and Section 21.

## Run locally
```
cd backend/services/safety-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port <see docker-compose.yml>
```

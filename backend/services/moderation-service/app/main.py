"""
moderation-service — see README.md for scope and R&D doc references.
Phase 0: infrastructure only. Real endpoints land in the phase noted
in this service's README / the root Build_Prompt_Sequence.md.
"""
from fastapi import FastAPI

app = FastAPI(title="moderation-service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "moderation-service"}

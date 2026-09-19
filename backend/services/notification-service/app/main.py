"""
notification-service — see README.md for scope and R&D doc references.
Phase 0: infrastructure only. Real endpoints land in the phase noted
in this service's README / the root Build_Prompt_Sequence.md.
"""
import uuid

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

INTERNAL_SECRET = __import__("os").environ.get("INTERNAL_SHARED_SECRET", "dev-only-change-me")

app = FastAPI(title="notification-service", version="0.1.0")


class ActivityAlertRequest(BaseModel):
    recipient_ids: list[uuid.UUID] = Field(max_length=500)
    meetup_id: uuid.UUID
    category: str


@app.post("/internal/activity-alerts", status_code=202)
def queue_activity_alerts(payload: ActivityAlertRequest, x_internal_secret: str = Header(default="")) -> dict[str, int]:
    if x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(status_code=401, detail="Invalid internal credential")
    # Delivery adapters (push/email) are intentionally downstream of this
    # consent-filtered handoff; this service never receives location data.
    return {"accepted": len(set(payload.recipient_ids))}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "notification-service"}

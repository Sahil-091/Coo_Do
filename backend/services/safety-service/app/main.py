"""Safety service: classify text before any LLM, public display, or persistence boundary."""
import secrets
import uuid
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.gemini_classifier import PROMPT_VERSION, ClassifierUnavailable, classify_text
from app.resources import load_resources
from app.support_scripts import SupportScript, script_for
from db.base import SessionLocal
from db.models.safety import EscalationStatus, SafetyEvent, SafetyFlagLevel, SafetySource

app = FastAPI(title="safety-service", version="0.5.0")


class SafetyCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    source: SafetySource
    user_ref: uuid.UUID


class SupportResponse(BaseModel):
    id: str
    title: str
    body: str
    urgency: str


class SafetyCheckResponse(BaseModel):
    flag_level: str
    safety_event_id: uuid.UUID | None
    support: SupportResponse | None


class ReviewEventResponse(BaseModel):
    id: uuid.UUID
    user_ref: uuid.UUID
    flag_level: str
    source: str
    response_template_id: str
    classifier_model: str
    classifier_prompt_version: str
    escalation_status: str
    reviewer_ref: uuid.UUID | None
    created_at: datetime
    reviewed_at: datetime | None


class ReviewUpdateRequest(BaseModel):
    reviewer_ref: uuid.UUID
    escalation_status: EscalationStatus


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_internal_secret(x_internal_secret: str = Header(default="")) -> None:
    if not secrets.compare_digest(x_internal_secret, settings.internal_shared_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal credential")


def verify_reviewer_token(x_safety_reviewer_token: str = Header(default="")) -> None:
    if not settings.safety_reviewer_token or not secrets.compare_digest(
        x_safety_reviewer_token, settings.safety_reviewer_token
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reviewer credential")


def get_reviewer_db():
    if not settings.reviewer_database_url:
        raise HTTPException(status_code=503, detail="Reviewer database access is not configured")
    engine = create_engine(settings.reviewer_database_url, pool_pre_ping=True)
    reviewer_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = reviewer_session()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def as_support_response(script: SupportScript | None) -> SupportResponse | None:
    if not script:
        return None
    return SupportResponse(id=script.id, title=script.title, body=script.body, urgency=script.urgency)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "safety-service"}


@app.get("/v1/resources")
def resources() -> dict[str, object]:
    try:
        configured = load_resources(settings.safety_resources_file)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Crisis resource configuration is unavailable") from exc
    return configured.model_dump()


@app.post(
    "/v1/check-text",
    response_model=SafetyCheckResponse,
    dependencies=[Depends(verify_internal_secret)],
)
def check_text(payload: SafetyCheckRequest, db: Session = Depends(get_db)) -> SafetyCheckResponse:
    """Classify before the caller can send this text to an LLM or store/display it.

    Sections 10 and 14-G intentionally prohibit auto-contacting trusted people,
    diagnoses, confidentiality promises, and model-written support. A detected flag
    only returns a deterministic script and resource path; human review is separate.
    """
    try:
        flag_level = classify_text(payload.text)
    except ClassifierUnavailable as exc:
        # Do not silently classify a provider failure as "none". The caller must fail
        # closed, stop the downstream operation, and show the resource display.
        raise HTTPException(status_code=503, detail="Safety screening is temporarily unavailable") from exc

    script = script_for(flag_level)
    if flag_level == "none":
        return SafetyCheckResponse(flag_level="none", safety_event_id=None, support=None)

    is_crisis = flag_level == "crisis"
    event = SafetyEvent(
        user_ref=payload.user_ref,
        flag_level=SafetyFlagLevel(flag_level),
        source=payload.source,
        response_template_id=script.id if script else "unavailable",
        # Minimize sensitive retention: only crisis flags retain the text for review.
        flagged_text=payload.text if is_crisis else None,
        escalation_status=(
            EscalationStatus.HUMAN_REVIEW_PENDING if is_crisis else EscalationStatus.RESOURCE_SHOWN
        ),
        classifier_model=settings.gemini_model,
        classifier_prompt_version=PROMPT_VERSION,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return SafetyCheckResponse(
        flag_level=flag_level, safety_event_id=event.id, support=as_support_response(script)
    )


@app.get(
    "/internal/review/events",
    response_model=list[ReviewEventResponse],
    dependencies=[Depends(verify_reviewer_token)],
)
def list_review_events(db: Session = Depends(get_reviewer_db)) -> list[ReviewEventResponse]:
    # Select explicit metadata columns. The reviewer role is never granted flagged_text.
    rows = db.execute(
        select(
            SafetyEvent.id, SafetyEvent.user_ref, SafetyEvent.flag_level, SafetyEvent.source,
            SafetyEvent.response_template_id, SafetyEvent.classifier_model,
            SafetyEvent.classifier_prompt_version, SafetyEvent.escalation_status,
            SafetyEvent.reviewer_ref, SafetyEvent.created_at, SafetyEvent.reviewed_at,
        ).order_by(SafetyEvent.created_at.desc())
    ).all()
    return [ReviewEventResponse.model_validate(row._mapping) for row in rows]


@app.patch(
    "/internal/review/events/{event_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_reviewer_token)],
)
def update_review_event(
    event_id: uuid.UUID, payload: ReviewUpdateRequest, db: Session = Depends(get_reviewer_db)
) -> None:
    result = db.execute(
        update(SafetyEvent)
        .where(SafetyEvent.id == event_id)
        .values(
            escalation_status=payload.escalation_status,
            reviewer_ref=payload.reviewer_ref,
            reviewed_at=datetime.now(UTC),
        )
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=404, detail="Safety event not found")
    db.commit()

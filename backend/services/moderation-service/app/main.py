"""Phase 12 anonymous rooms and pre-publication moderation pipeline."""
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.classifier import classify_non_safety
from app.config import settings
from app.db import get_db
from app.internal_clients import DependencyUnavailable, account_created_at, screen_self_harm
from app.schemas import (
    ContentScreenRequest,
    ContentScreenResponse,
    GuidelinesAcceptanceRequest,
    PostCreateRequest,
    PostResponse,
    PostSubmitResponse,
    ReportCreateRequest,
    ReviewDecisionRequest,
    ReviewEventResponse,
    RoomCreateRequest,
    RoomResponse,
)
from app.security import verify_internal_secret, verify_reviewer_token
from db.models.moderation import (
    CommunityGuidelinesAcceptance,
    CommunityPost,
    CommunityPostStatus,
    CommunityReport,
    CommunityRoom,
    ModerationEvent,
    ModerationReviewStatus,
)

app = FastAPI(title="moderation-service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "moderation-service"}


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


def _new_account(user_id: uuid.UUID) -> bool:
    try:
        created_at = account_created_at(user_id)
    except DependencyUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    return datetime.now(UTC) - created_at < timedelta(days=7)


def _rate_limit_posts(db: Session, user_id: uuid.UUID) -> None:
    limit = 3 if _new_account(user_id) else 10
    recent = db.query(CommunityPost).filter(
        CommunityPost.author_user_ref == user_id,
        CommunityPost.created_at >= datetime.now(UTC) - timedelta(hours=1),
    ).count()
    if recent >= limit:
        raise HTTPException(status_code=429, detail="Posting limit reached. Please try again later.")


def _rate_limit_rooms(db: Session, user_id: uuid.UUID) -> None:
    limit = 1 if _new_account(user_id) else 3
    recent = db.query(CommunityRoom).filter(
        CommunityRoom.created_by_user_ref == user_id,
        CommunityRoom.created_at >= datetime.now(UTC) - timedelta(days=1),
    ).count()
    if recent >= limit:
        raise HTTPException(status_code=429, detail="Room creation limit reached. Please try again tomorrow.")


def _queue_event(db: Session, post: CommunityPost, reasons: list[str], self_harm_level: str) -> None:
    db.add(ModerationEvent(post_id=post.id, reasons=reasons, self_harm_level=self_harm_level))


@app.post("/internal/moderation/screen", response_model=ContentScreenResponse, dependencies=[Depends(verify_internal_secret)])
def screen_content(payload: ContentScreenRequest) -> ContentScreenResponse:
    """Shared Phase 12 screen for content shapes beyond anonymous posts.

    Callers must fail closed when `held` is true; raw activity text is not
    duplicated here, preventing a second sensitive-content store.
    """
    try:
        safety = screen_self_harm(payload.text, payload.user_id)
    except DependencyUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    safety_level = str(safety.get("flag_level", "crisis"))
    reasons = classify_non_safety(payload.text)
    if safety_level != "none":
        reasons.append("self_harm_or_crisis_language")
    return ContentScreenResponse(held=bool(reasons), reasons=reasons, safety_flag_level=safety_level)


@app.get("/internal/community/rooms", response_model=list[RoomResponse], dependencies=[Depends(verify_internal_secret)])
def list_rooms(db: Session = Depends(get_db)) -> list[RoomResponse]:
    rows = db.query(CommunityRoom).filter(CommunityRoom.is_open.is_(True)).order_by(CommunityRoom.created_at.desc()).all()
    return [RoomResponse(id=row.id, topic=row.topic, created_at=row.created_at) for row in rows]


@app.post("/internal/community/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_internal_secret)])
def create_room(payload: RoomCreateRequest, db: Session = Depends(get_db)) -> RoomResponse:
    _rate_limit_rooms(db, payload.user_id)
    room = CommunityRoom(topic=payload.topic, created_by_user_ref=payload.user_id)
    db.add(room)
    db.commit()
    db.refresh(room)
    return RoomResponse(id=room.id, topic=room.topic, created_at=room.created_at)


@app.post("/internal/community/guidelines/accept", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_internal_secret)])
def accept_guidelines(payload: GuidelinesAcceptanceRequest, db: Session = Depends(get_db)) -> None:
    existing = db.query(CommunityGuidelinesAcceptance).filter(
        CommunityGuidelinesAcceptance.user_ref == payload.user_id,
        CommunityGuidelinesAcceptance.guidelines_version == payload.guidelines_version,
    ).first()
    if existing is None:
        db.add(CommunityGuidelinesAcceptance(user_ref=payload.user_id, guidelines_version=payload.guidelines_version))
        db.commit()


@app.get("/internal/community/rooms/{room_id}/posts", response_model=list[PostResponse], dependencies=[Depends(verify_internal_secret)])
def list_posts(room_id: uuid.UUID, db: Session = Depends(get_db)) -> list[PostResponse]:
    if db.get(CommunityRoom, room_id) is None:
        raise HTTPException(status_code=404, detail="Room not found.")
    rows = db.query(CommunityPost).filter(
        CommunityPost.room_id == room_id, CommunityPost.status == CommunityPostStatus.VISIBLE
    ).order_by(CommunityPost.created_at.asc()).all()
    return [PostResponse(id=row.id, body=row.body, created_at=row.created_at) for row in rows]


@app.post("/internal/community/rooms/{room_id}/posts", response_model=PostSubmitResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_internal_secret)])
def create_post(room_id: uuid.UUID, payload: PostCreateRequest, db: Session = Depends(get_db)) -> PostSubmitResponse:
    room = db.get(CommunityRoom, room_id)
    if room is None or not room.is_open:
        raise HTTPException(status_code=404, detail="Room not found.")
    accepted = db.query(CommunityGuidelinesAcceptance).filter(
        CommunityGuidelinesAcceptance.user_ref == payload.user_id,
        CommunityGuidelinesAcceptance.guidelines_version == payload.guidelines_version,
    ).first()
    if accepted is None:
        raise HTTPException(status_code=409, detail="Read and accept the community guidelines before posting.")
    _rate_limit_posts(db, payload.user_id)
    try:
        safety = screen_self_harm(payload.body, payload.user_id)
    except DependencyUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    safety_level = str(safety.get("flag_level", "crisis"))
    reasons = classify_non_safety(payload.body)
    if safety_level != "none":
        reasons.append("self_harm_or_crisis_language")
    held = bool(reasons)
    post = CommunityPost(
        room_id=room_id,
        author_user_ref=payload.user_id,
        body=payload.body.strip(),
        status=CommunityPostStatus.HELD_FOR_REVIEW if held else CommunityPostStatus.VISIBLE,
    )
    db.add(post)
    db.flush()
    if held:
        _queue_event(db, post, reasons, safety_level)
    db.commit()
    db.refresh(post)
    return PostSubmitResponse(
        post=PostResponse(id=post.id, body=post.body, created_at=post.created_at) if not held else None,
        held_for_review=held,
        safety_flag_level=safety_level,
    )


@app.post("/internal/community/posts/{post_id}/reports", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_internal_secret)])
def report_post(post_id: uuid.UUID, payload: ReportCreateRequest, db: Session = Depends(get_db)) -> None:
    post = db.get(CommunityPost, post_id)
    if post is None or post.author_user_ref == payload.user_id:
        raise HTTPException(status_code=404, detail="Post not found.")
    try:
        db.add(CommunityReport(post_id=post_id, reporter_user_ref=payload.user_id, category=payload.category))
        post.status = CommunityPostStatus.HELD_FOR_REVIEW
        if db.query(ModerationEvent).filter(ModerationEvent.post_id == post_id).first() is None:
            _queue_event(db, post, [f"member_report:{payload.category.value}"], "none")
        db.commit()
    except IntegrityError:
        db.rollback()  # A duplicate report is deliberately idempotent.


@app.get("/internal/review/events", response_model=list[ReviewEventResponse], dependencies=[Depends(verify_reviewer_token)])
def list_review_events(db: Session = Depends(get_reviewer_db)) -> list[ReviewEventResponse]:
    rows = db.query(ModerationEvent, CommunityPost).join(CommunityPost, CommunityPost.id == ModerationEvent.post_id).filter(
        ModerationEvent.review_status == ModerationReviewStatus.PENDING
    ).order_by(ModerationEvent.created_at.asc()).all()
    return [ReviewEventResponse(id=event.id, post_id=post.id, room_id=post.room_id, body=post.body, reasons=event.reasons, self_harm_level=event.self_harm_level, review_status=event.review_status, created_at=event.created_at) for event, post in rows]


@app.patch("/internal/review/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_reviewer_token)])
def review_event(event_id: uuid.UUID, payload: ReviewDecisionRequest, db: Session = Depends(get_reviewer_db)) -> None:
    if payload.decision not in {ModerationReviewStatus.APPROVED, ModerationReviewStatus.REMOVED}:
        raise HTTPException(status_code=422, detail="A review must approve or remove the post.")
    event = db.get(ModerationEvent, event_id)
    if event is None or event.review_status != ModerationReviewStatus.PENDING:
        raise HTTPException(status_code=404, detail="Pending review event not found.")
    post = db.get(CommunityPost, event.post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    event.review_status = payload.decision
    event.reviewer_ref = payload.reviewer_ref
    event.reviewed_at = datetime.now(UTC)
    post.status = CommunityPostStatus.VISIBLE if payload.decision == ModerationReviewStatus.APPROVED else CommunityPostStatus.REMOVED
    db.commit()

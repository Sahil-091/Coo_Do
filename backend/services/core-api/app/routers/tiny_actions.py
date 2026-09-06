import random
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    ActionAttemptCreateRequest,
    ActionAttemptResponse,
    ActionAttemptStatusIn,
    ActionAttemptSubmitResponse,
    SuggestionResponse,
    TinyActionRung,
)
from app.security import verify_internal_secret
from db.models.core import ActionAttempt, ActionAttemptStatus, TinyAction, User

router = APIRouter(
    prefix="/internal/users",
    tags=["tiny-actions"],
    dependencies=[Depends(verify_internal_secret)],
)

# "Multiple times in a row" trigger for the repeated-failure safety
# signal (R&D doc Section 5.3 — required behavior, not optional polish).
REPEATED_FAILURE_THRESHOLD = 3


def _get_user_or_404(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def _fetch_ladder(db: Session, any_rung_id: uuid.UUID) -> list[TinyAction]:
    """Given any rung's id, return every rung in its ladder, easiest first.
    Walks the parent chain up to the root (hardest rung), then walks
    back down to collect every descendant — the table is small enough
    (see seed script) that this is simpler and cheaper than a recursive
    CTE, and doesn't assume a fixed ladder depth."""
    rung = db.get(TinyAction, any_rung_id)
    if rung is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tiny action not found.")

    root = rung
    while root.ladder_parent_id is not None:
        root = db.get(TinyAction, root.ladder_parent_id)

    all_rungs = {root.id: root}
    frontier = [root.id]
    while frontier:
        children = db.query(TinyAction).filter(TinyAction.ladder_parent_id.in_(frontier)).all()
        frontier = []
        for child in children:
            if child.id not in all_rungs:
                all_rungs[child.id] = child
                frontier.append(child.id)

    return sorted(all_rungs.values(), key=lambda r: r.difficulty_level)


def _detect_repeated_floor_failures(db: Session, user_id: uuid.UUID) -> bool:
    """
    The required safety signal: has the student's last N *outcomes*
    (completed/skipped/reduced — NOT the automatic SUGGESTED rows the
    suggestion endpoint logs every time it shows something) all been
    'reduced, and already at the easiest rung with nowhere further to
    go'? Deliberately checked across ANY ladder, not just the same
    one — the meaningful pattern is 'can't manage even the smallest
    version of things right now', not 'struggling with this one
    specific ladder'. See this phase's build notes for the reasoning.

    SUGGESTED rows are explicitly excluded from this query — every real
    "reduce" in actual usage is preceded by a fresh suggestion fetch, so
    including SUGGESTED here would interleave it between REDUCED rows
    and break the streak on every realistic interaction pattern. (This
    was an actual bug, caught by a test simulating the real UI flow
    rather than calling the endpoint in isolation — see test_action_attempts.py.)
    """
    recent = (
        db.query(ActionAttempt, TinyAction.difficulty_level)
        .join(TinyAction, ActionAttempt.tiny_action_id == TinyAction.id)
        .filter(
            ActionAttempt.user_id == user_id,
            ActionAttempt.status != ActionAttemptStatus.SUGGESTED,
        )
        .order_by(ActionAttempt.created_at.desc())
        .limit(REPEATED_FAILURE_THRESHOLD)
        .all()
    )
    if len(recent) < REPEATED_FAILURE_THRESHOLD:
        return False
    return all(
        attempt.status == ActionAttemptStatus.REDUCED and difficulty_level == 1
        for attempt, difficulty_level in recent
    )


@router.get("/{user_id}/tiny-actions/suggestion", response_model=SuggestionResponse)
def get_suggestion(user_id: uuid.UUID, db: Session = Depends(get_db)) -> SuggestionResponse:
    """
    Picks a random ladder and returns ALL of its rungs in one response —
    the frontend navigates "make it bigger"/"make it smaller" entirely
    client-side against this already-fetched ladder, no further network
    calls needed for navigation. Logs a SUGGESTED attempt for the
    default (middle, difficulty_level=2) rung.
    """
    _get_user_or_404(db, user_id)

    root_ids = [row[0] for row in db.query(TinyAction.id).filter(TinyAction.ladder_parent_id.is_(None)).all()]
    if not root_ids:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No tiny actions are seeded yet.",
        )
    chosen_root_id = random.choice(root_ids)
    ladder = _fetch_ladder(db, chosen_root_id)

    default_rung = next((r for r in ladder if r.difficulty_level == 2), ladder[len(ladder) // 2])

    suggested_attempt = ActionAttempt(
        user_id=user_id, tiny_action_id=default_rung.id, status=ActionAttemptStatus.SUGGESTED
    )
    db.add(suggested_attempt)
    db.commit()
    db.refresh(suggested_attempt)

    return SuggestionResponse(
        ladder=[
            TinyActionRung(
                id=r.id, difficulty_level=r.difficulty_level, title=r.title, description=r.description
            )
            for r in ladder
        ],
        suggested_attempt_id=suggested_attempt.id,
    )


_STATUS_MAP = {
    ActionAttemptStatusIn.COMPLETED: ActionAttemptStatus.COMPLETED,
    ActionAttemptStatusIn.SKIPPED: ActionAttemptStatus.SKIPPED,
    ActionAttemptStatusIn.REDUCED: ActionAttemptStatus.REDUCED,
}


@router.post(
    "/{user_id}/action-attempts", response_model=ActionAttemptSubmitResponse, status_code=201
)
def log_action_attempt(
    user_id: uuid.UUID, payload: ActionAttemptCreateRequest, db: Session = Depends(get_db)
) -> ActionAttemptSubmitResponse:
    _get_user_or_404(db, user_id)
    tiny_action = db.get(TinyAction, payload.tiny_action_id)
    if tiny_action is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tiny action not found.")

    attempt = ActionAttempt(
        user_id=user_id,
        tiny_action_id=payload.tiny_action_id,
        status=_STATUS_MAP[payload.status],
        related_checkin_id=payload.related_checkin_id,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    show_support_nudge = _detect_repeated_floor_failures(db, user_id)

    return ActionAttemptSubmitResponse(
        attempt=ActionAttemptResponse(
            id=attempt.id,
            tiny_action_id=attempt.tiny_action_id,
            status=attempt.status.value,
            related_checkin_id=attempt.related_checkin_id,
            created_at=attempt.created_at,
        ),
        show_support_nudge=show_support_nudge,
    )

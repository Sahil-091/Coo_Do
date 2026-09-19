"""Phase 8 private journal. Decryption happens only for the entry owner."""
import uuid
from datetime import UTC, datetime, timedelta

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.journal_crypto import build_journal_cipher
from app.schemas import (
    JournalComparisonResponse,
    JournalEntryCreate,
    JournalEntryResponse,
    JournalExportResponse,
    RealLifeIndicatorResponse,
    ResourceOpenResponse,
)
from app.security import verify_internal_secret
from db.models.core import (
    ActionAttempt,
    ActionAttemptStatus,
    ActivityParticipant,
    HelpSeekingAction,
    JournalEntry,
    ProfessionalResource,
    User,
)

router = APIRouter(prefix="/internal/users", tags=["journal"], dependencies=[Depends(verify_internal_secret)])

try:
    CIPHER = build_journal_cipher(settings.journal_encryption_keys)
except (TypeError, ValueError) as exc:
    raise RuntimeError("JOURNAL_ENCRYPTION_KEYS must contain valid Fernet keys.") from exc


def _owner(db: Session, user_id: uuid.UUID) -> None:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found.")


def _response(entry: JournalEntry) -> JournalEntryResponse:
    try:
        body = CIPHER.decrypt(entry.encrypted_body.encode()).decode()
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Journal entry cannot be read.") from exc
    return JournalEntryResponse(id=entry.id, body=body, created_at=entry.created_at, updated_at=entry.updated_at)


@router.get("/{user_id}/journal", response_model=list[JournalEntryResponse])
def list_entries(user_id: uuid.UUID, db: Session = Depends(get_db)) -> list[JournalEntryResponse]:
    _owner(db, user_id)
    rows = db.query(JournalEntry).filter(JournalEntry.user_id == user_id).order_by(JournalEntry.created_at.desc()).all()
    return [_response(row) for row in rows]


@router.post("/{user_id}/journal", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(user_id: uuid.UUID, payload: JournalEntryCreate, db: Session = Depends(get_db)) -> JournalEntryResponse:
    _owner(db, user_id)
    entry = JournalEntry(
        user_id=user_id,
        encrypted_body=CIPHER.encrypt(payload.body.strip().encode()).decode(),
        encryption_version="fernet-multikey-v1",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _response(entry)


@router.get("/{user_id}/journal/export", response_model=JournalExportResponse)
def export_entries(user_id: uuid.UUID, db: Session = Depends(get_db)) -> JournalExportResponse:
    """Return the requesting student's decrypted journal as a portable export.

    This endpoint remains behind the internal-server boundary; the browser
    reaches it only through the signed-in user's Next.js server action.
    """
    _owner(db, user_id)
    rows = (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == user_id)
        .order_by(JournalEntry.created_at.asc())
        .all()
    )
    return JournalExportResponse(entries=[_response(row) for row in rows])


@router.delete("/{user_id}/journal/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(user_id: uuid.UUID, entry_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    _owner(db, user_id)
    entry = (
        db.query(JournalEntry)
        .filter(JournalEntry.id == entry_id, JournalEntry.user_id == user_id)
        .one_or_none()
    )
    if entry is None:
        # Do not disclose whether another student's entry id exists.
        raise HTTPException(status_code=404, detail="Journal entry not found.")
    db.delete(entry)
    db.commit()


@router.delete("/{user_id}/journal", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_entries(user_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    _owner(db, user_id)
    db.query(JournalEntry).filter(JournalEntry.user_id == user_id).delete(synchronize_session=False)
    db.commit()


@router.post("/{user_id}/professional-resources/{resource_id}/open", response_model=ResourceOpenResponse)
def open_professional_resource(
    user_id: uuid.UUID, resource_id: uuid.UUID, db: Session = Depends(get_db)
) -> ResourceOpenResponse:
    """Record an explicit student-initiated open/call, then return its URI.

    Merely viewing a check-in or the help directory never creates this event.
    The event represents the student's intentional click on a curated resource,
    which is the only help-seeking signal shown in Phase 8's indicators.
    """
    _owner(db, user_id)
    resource = db.get(ProfessionalResource, resource_id)
    if resource is None or not resource.is_active or not resource.contact_uri:
        raise HTTPException(status_code=404, detail="Professional resource is unavailable.")

    action_type = "call_resource" if resource.contact_uri.startswith("tel:") else "open_resource"
    db.add(HelpSeekingAction(user_id=user_id, resource_id=resource.id, action_type=action_type))
    db.commit()
    return ResourceOpenResponse(destination=resource.contact_uri, action_type=action_type)


@router.get("/{user_id}/journal/comparisons", response_model=list[JournalComparisonResponse])
def comparisons(user_id: uuid.UUID, db: Session = Depends(get_db)) -> list[JournalComparisonResponse]:
    _owner(db, user_id)
    now = datetime.now(UTC)
    result = []
    for days in (7, 30, 90):
        entries = db.query(JournalEntry).filter(JournalEntry.user_id == user_id, JournalEntry.created_at >= now - timedelta(days=days)).order_by(JournalEntry.created_at).all()
        if not entries:
            narrative = f"There are no reflections from the last {days} days yet. When you are ready, one sentence is enough."
        elif len(entries) == 1:
            narrative = "You made a reflection in this period. Return later to notice what changes in your own words."
        else:
            first, latest = _response(entries[0]).body, _response(entries[-1]).body
            narrative = f"In this period, you began with: “{first[:140]}” Your most recent reflection begins: “{latest[:140]}”"
        result.append(JournalComparisonResponse(window_days=days, narrative=narrative))
    return result


@router.get("/{user_id}/real-life-indicators", response_model=list[RealLifeIndicatorResponse])
def indicators(user_id: uuid.UUID, db: Session = Depends(get_db)) -> list[RealLifeIndicatorResponse]:
    _owner(db, user_id)
    completed = db.query(ActionAttempt).filter(ActionAttempt.user_id == user_id, ActionAttempt.status == ActionAttemptStatus.COMPLETED).count()
    # Count only the two event types whose database constraint documents an
    # intentional Professional Help resource interaction.  The explicit
    # filter is defense in depth if the constrained vocabulary ever changes.
    help_actions = (
        db.query(HelpSeekingAction)
        .filter(
            HelpSeekingAction.user_id == user_id,
            HelpSeekingAction.action_type.in_(("open_resource", "call_resource")),
        )
        .count()
    )
    activity_joins = (
        db.query(ActivityParticipant)
        .filter(ActivityParticipant.user_id == user_id)
        .count()
    )
    return [
        RealLifeIndicatorResponse(key="tiny_actions", sentence=f"Tiny actions completed: {completed}."),
        RealLifeIndicatorResponse(key="activities", sentence=f"Virtual activities joined: {activity_joins}."),
        RealLifeIndicatorResponse(key="help_seeking", sentence=f"Help-seeking actions taken: {help_actions}."),
    ]

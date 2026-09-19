"""Phase 10 student-initiated trusted-person outreach.

There is deliberately no route or job that contacts a trusted person from a
check-in, trend, period of inactivity, or safety event. The only handoff is a
student's explicit tap, which opens their own SMS/email composer.
"""
import json
import uuid
from urllib.parse import quote

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.schemas import (
    TrustedContactChannel,
    TrustedContactCreate,
    TrustedContactResponse,
    TrustedOutreachRequest,
    TrustedOutreachResponse,
)
from app.security import verify_internal_secret
from app.trusted_contact_crypto import build_trusted_contact_cipher
from db.models.core import TrustedContact, TrustedContactScenario, User

router = APIRouter(
    prefix="/internal/users",
    tags=["trusted-contacts"],
    dependencies=[Depends(verify_internal_secret)],
)

try:
    CIPHER = build_trusted_contact_cipher(settings.trusted_contact_encryption_keys)
except (TypeError, ValueError) as exc:
    raise RuntimeError("TRUSTED_CONTACT_ENCRYPTION_KEYS must contain valid Fernet keys.") from exc

OUTREACH_COPY: dict[TrustedContactScenario, str] = {
    TrustedContactScenario.FEELING_OVERWHELMED: "I'm feeling overwhelmed right now. If you're able, could we talk?",
    TrustedContactScenario.NEED_TO_TALK: "I could use someone to talk to. Are you available for a chat?",
    TrustedContactScenario.PRACTICAL_SUPPORT: "I could use some practical support right now. Are you able to help me think through it?",
    TrustedContactScenario.URGENT_BUT_NOT_EMERGENCY: "I need support soon. If you're available, could you get in touch with me?",
}


def _owner(db: Session, user_id: uuid.UUID) -> None:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found.")


def _decrypt(contact: TrustedContact) -> dict[str, str]:
    try:
        payload = json.loads(CIPHER.decrypt(contact.encrypted_payload.encode()).decode())
        if not all(isinstance(payload.get(key), str) for key in ("display_name", "channel", "contact_value")):
            raise ValueError("invalid trusted contact payload")
        return payload
    except (InvalidToken, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Trusted contact cannot be read.") from exc


def _response(contact: TrustedContact) -> TrustedContactResponse:
    payload = _decrypt(contact)
    return TrustedContactResponse(
        id=contact.id,
        display_name=payload["display_name"],
        relationship=contact.relationship,
        channel=TrustedContactChannel(payload["channel"]),
        allowed_scenarios=[TrustedContactScenario(value) for value in contact.allowed_scenarios],
        created_at=contact.created_at,
        updated_at=contact.updated_at,
    )


@router.get("/{user_id}/trusted-contacts", response_model=list[TrustedContactResponse])
def list_contacts(user_id: uuid.UUID, db: Session = Depends(get_db)) -> list[TrustedContactResponse]:
    _owner(db, user_id)
    contacts = (
        db.query(TrustedContact)
        .filter(TrustedContact.user_id == user_id)
        .order_by(TrustedContact.created_at.desc())
        .all()
    )
    return [_response(contact) for contact in contacts]


@router.post("/{user_id}/trusted-contacts", response_model=TrustedContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    user_id: uuid.UUID, payload: TrustedContactCreate, db: Session = Depends(get_db)
) -> TrustedContactResponse:
    _owner(db, user_id)
    # A small cap prevents this private feature becoming an unbounded contact
    # book and limits the sensitivity of data retained in this product.
    if db.query(TrustedContact).filter(TrustedContact.user_id == user_id).count() >= 12:
        raise HTTPException(status_code=429, detail="You can save up to 12 trusted contacts.")
    encrypted_payload = CIPHER.encrypt(
        json.dumps(
            {
                "display_name": payload.display_name,
                "channel": payload.channel,
                "contact_value": payload.contact_value,
            },
            separators=(",", ":"),
        ).encode()
    ).decode()
    contact = TrustedContact(
        user_id=user_id,
        relationship=payload.relationship,
        allowed_scenarios=[scenario.value for scenario in payload.allowed_scenarios],
        encrypted_payload=encrypted_payload,
        encryption_version="fernet-multikey-v1",
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return _response(contact)


@router.delete("/{user_id}/trusted-contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(user_id: uuid.UUID, contact_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    _owner(db, user_id)
    contact = (
        db.query(TrustedContact)
        .filter(TrustedContact.id == contact_id, TrustedContact.user_id == user_id)
        .one_or_none()
    )
    if contact is None:
        raise HTTPException(status_code=404, detail="Trusted contact not found.")
    db.delete(contact)
    db.commit()


@router.post(
    "/{user_id}/trusted-contacts/{contact_id}/outreach",
    response_model=TrustedOutreachResponse,
)
def prepare_outreach(
    user_id: uuid.UUID,
    contact_id: uuid.UUID,
    payload: TrustedOutreachRequest,
    db: Session = Depends(get_db),
) -> TrustedOutreachResponse:
    """Prepare a native composer destination after an explicit student action.

    This does not send any network notification. The browser navigates to an
    SMS/email composer and the student retains the final send decision.
    """
    _owner(db, user_id)
    contact = (
        db.query(TrustedContact)
        .filter(TrustedContact.id == contact_id, TrustedContact.user_id == user_id)
        .one_or_none()
    )
    if contact is None:
        raise HTTPException(status_code=404, detail="Trusted contact not found.")
    if payload.scenario.value not in contact.allowed_scenarios:
        raise HTTPException(status_code=403, detail="This contact is not approved for that situation.")
    decrypted = _decrypt(contact)
    try:
        channel = TrustedContactChannel(decrypted["channel"])
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Trusted contact cannot be used.") from exc
    message = OUTREACH_COPY[payload.scenario]
    if channel == TrustedContactChannel.SMS:
        destination = f"sms:{quote(decrypted['contact_value'], safe='+')}?body={quote(message)}"
    else:
        destination = f"mailto:{quote(decrypted['contact_value'], safe='@')}?subject={quote('Could we talk?')}&body={quote(message)}"
    return TrustedOutreachResponse(destination=destination, contact_name=decrypted["display_name"])

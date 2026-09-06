import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    AgeVerificationRequest,
    AgeVerificationResponse,
    ConsentStateResponse,
    ConsentUpsertRequest,
    DataRequestCreate,
    DataRequestResponse,
    DisplayNameRequest,
    PrivacySettingsRequest,
    PrivacySettingsResponse,
    UserStateResponse,
)
from app.security import verify_internal_secret
from db.models.core import ConsentRecord, ConsentType, DataRequest, PrivacySettings, User

router = APIRouter(
    prefix="/internal/users",
    tags=["users"],
    dependencies=[Depends(verify_internal_secret)],
)

MINIMUM_AGE = 18


def _get_user_or_404(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def _compute_age(dob: date, as_of: date | None = None) -> int:
    as_of = as_of or date.today()
    return as_of.year - dob.year - ((as_of.month, as_of.day) < (dob.month, dob.day))


@router.get("/{user_id}", response_model=UserStateResponse)
def get_user_state(user_id: uuid.UUID, db: Session = Depends(get_db)) -> UserStateResponse:
    user = _get_user_or_404(db, user_id)
    return UserStateResponse(
        user_id=user.id,
        email=user.email,
        age_verified=user.age_verified,
        pseudonymous_display_name=user.pseudonymous_display_name,
        created_at=user.created_at,
    )


@router.put("/{user_id}/age-verification", response_model=AgeVerificationResponse)
def submit_age_verification(
    user_id: uuid.UUID, payload: AgeVerificationRequest, db: Session = Depends(get_db)
) -> AgeVerificationResponse:
    """
    The hard gate (R&D doc Section 11/17): we RECORD the submitted date
    of birth regardless of outcome (an audit trail that the check was
    actually performed — see Section 11's reasoning on why this is worth
    the minor extra data retention), but `age_verified` only flips true
    at 18+. Nothing else in onboarding can complete for a user whose
    age_verified is false — enforced here server-side, not just by the
    frontend hiding the "continue" button.
    """
    user = _get_user_or_404(db, user_id)
    age = _compute_age(payload.date_of_birth)

    user.date_of_birth = payload.date_of_birth
    user.age_verified = age >= MINIMUM_AGE
    db.commit()

    return AgeVerificationResponse(age_verified=user.age_verified, minimum_age=MINIMUM_AGE)


@router.put("/{user_id}/display-name", response_model=UserStateResponse)
def set_display_name(
    user_id: uuid.UUID, payload: DisplayNameRequest, db: Session = Depends(get_db)
) -> UserStateResponse:
    user = _get_user_or_404(db, user_id)
    # Empty string is treated the same as null — both mean "no display
    # name set", never an empty-but-present string shown in the UI.
    user.pseudonymous_display_name = payload.pseudonymous_display_name or None
    db.commit()

    return UserStateResponse(
        user_id=user.id,
        email=user.email,
        age_verified=user.age_verified,
        pseudonymous_display_name=user.pseudonymous_display_name,
        created_at=user.created_at,
    )


@router.get("/{user_id}/consents", response_model=list[ConsentStateResponse])
def get_consents(user_id: uuid.UUID, db: Session = Depends(get_db)) -> list[ConsentStateResponse]:
    _get_user_or_404(db, user_id)

    # consent_records is append-only (R&D doc Section 11) — the current
    # state per type is whichever row is most recent. DISTINCT ON is the
    # clean way to express "latest row per group" in Postgres.
    latest_rows = (
        db.query(ConsentRecord)
        .filter(ConsentRecord.user_id == user_id)
        .distinct(ConsentRecord.consent_type)
        .order_by(ConsentRecord.consent_type, ConsentRecord.created_at.desc())
        .all()
    )
    latest_by_type = {row.consent_type: row for row in latest_rows}

    # Always return all known types, defaulting to "not granted" for any
    # type the user has never touched — never omit a type from the
    # response just because no row exists yet.
    return [
        ConsentStateResponse(
            consent_type=consent_type,
            granted=latest_by_type[consent_type].granted if consent_type in latest_by_type else False,
            updated_at=latest_by_type[consent_type].created_at if consent_type in latest_by_type else None,
        )
        for consent_type in ConsentType
    ]


@router.post("/{user_id}/consents", response_model=ConsentStateResponse, status_code=status.HTTP_201_CREATED)
def upsert_consent(
    user_id: uuid.UUID, payload: ConsentUpsertRequest, db: Session = Depends(get_db)
) -> ConsentStateResponse:
    _get_user_or_404(db, user_id)

    record = ConsentRecord(
        user_id=user_id, consent_type=payload.consent_type, granted=payload.granted
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ConsentStateResponse(
        consent_type=record.consent_type, granted=record.granted, updated_at=record.created_at
    )


@router.get("/{user_id}/privacy-settings", response_model=PrivacySettingsResponse)
def get_privacy_settings(
    user_id: uuid.UUID, db: Session = Depends(get_db)
) -> PrivacySettingsResponse:
    _get_user_or_404(db, user_id)
    settings_row = db.query(PrivacySettings).filter(PrivacySettings.user_id == user_id).first()
    if settings_row is None:
        # Shouldn't happen (register creates one), but fail gracefully
        # with defaults rather than a 500 if it somehow does.
        settings_row = PrivacySettings(user_id=user_id)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)

    return PrivacySettingsResponse(
        profile_visible_in_matching=settings_row.profile_visible_in_matching,
        display_name_visible_in_rooms=settings_row.display_name_visible_in_rooms,
        updated_at=settings_row.updated_at,
    )


@router.put("/{user_id}/privacy-settings", response_model=PrivacySettingsResponse)
def update_privacy_settings(
    user_id: uuid.UUID, payload: PrivacySettingsRequest, db: Session = Depends(get_db)
) -> PrivacySettingsResponse:
    _get_user_or_404(db, user_id)
    settings_row = db.query(PrivacySettings).filter(PrivacySettings.user_id == user_id).first()
    if settings_row is None:
        settings_row = PrivacySettings(user_id=user_id)
        db.add(settings_row)

    settings_row.profile_visible_in_matching = payload.profile_visible_in_matching
    settings_row.display_name_visible_in_rooms = payload.display_name_visible_in_rooms
    db.commit()
    db.refresh(settings_row)

    return PrivacySettingsResponse(
        profile_visible_in_matching=settings_row.profile_visible_in_matching,
        display_name_visible_in_rooms=settings_row.display_name_visible_in_rooms,
        updated_at=settings_row.updated_at,
    )


@router.get("/{user_id}/data-requests", response_model=list[DataRequestResponse])
def list_data_requests(
    user_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[DataRequestResponse]:
    _get_user_or_404(db, user_id)
    rows = (
        db.query(DataRequest)
        .filter(DataRequest.user_id == user_id)
        .order_by(DataRequest.created_at.desc())
        .all()
    )
    return [
        DataRequestResponse(
            id=r.id,
            request_type=r.request_type,
            status=r.status,
            created_at=r.created_at,
            completed_at=r.completed_at,
        )
        for r in rows
    ]


@router.post(
    "/{user_id}/data-requests", response_model=DataRequestResponse, status_code=status.HTTP_201_CREATED
)
def create_data_request(
    user_id: uuid.UUID, payload: DataRequestCreate, db: Session = Depends(get_db)
) -> DataRequestResponse:
    """
    Phase 2 scope: record-keeping only. This does NOT trigger any
    automated export/deletion pipeline — see DataRequest's docstring.
    A real notification-to-admin step belongs here eventually; for now
    this just creates the auditable record the Privacy Center UI needs.
    """
    _get_user_or_404(db, user_id)
    request_row = DataRequest(user_id=user_id, request_type=payload.request_type)
    db.add(request_row)
    db.commit()
    db.refresh(request_row)

    return DataRequestResponse(
        id=request_row.id,
        request_type=request_row.request_type,
        status=request_row.status,
        created_at=request_row.created_at,
        completed_at=request_row.completed_at,
    )

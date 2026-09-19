from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    RegisterRequest,
    RegisterResponse,
    UserStateResponse,
    VerifyCredentialsRequest,
)
from app.security import hash_password, verify_internal_secret, verify_password
from db.models.core import PrivacySettings, User

router = APIRouter(
    prefix="/internal/auth",
    tags=["auth"],
    dependencies=[Depends(verify_internal_secret)],
)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing is not None:
        # Deliberately generic — do not reveal *which* field was the
        # problem beyond "this email is taken", which is unavoidable for
        # a registration flow (unlike login, where we stay fully generic).
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()  # populate user.id before creating the dependent row

    # Every user gets a privacy_settings row at creation, defaults closed
    # (opt-in, not opt-out) — see R&D doc Section 11.
    db.add(PrivacySettings(user_id=user.id))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from None

    return RegisterResponse(user_id=user.id)


@router.post("/verify", response_model=UserStateResponse)
def verify_credentials(
    payload: VerifyCredentialsRequest, db: Session = Depends(get_db)
) -> UserStateResponse:
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    # Constant-shape failure regardless of whether the email exists or
    # the password was wrong — never let a caller distinguish the two,
    # that's how account enumeration happens.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    return UserStateResponse(
        user_id=user.id,
        email=user.email,
        age_verified=user.age_verified,
        pseudonymous_display_name=user.pseudonymous_display_name,
        created_at=user.created_at,
    )

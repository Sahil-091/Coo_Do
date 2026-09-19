"""Core-api-owned profile data exposed only to the trusted matching service."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    MatchingCandidateInternal,
    MatchingCandidatePoolResponse,
    MatchingProfileRequest,
    MatchingProfileResponse,
)
from app.security import verify_internal_secret
from db.models.core import ConsentRecord, ConsentType, PrivacySettings, Profile, User

router = APIRouter(
    prefix="/internal",
    tags=["matching-profile"],
    dependencies=[Depends(verify_internal_secret)],
)


def _latest_matching_consent_is_granted(db: Session, user_id: uuid.UUID) -> bool:
    row = (
        db.query(ConsentRecord)
        .filter(
            ConsentRecord.user_id == user_id,
            ConsentRecord.consent_type == ConsentType.MATCHING_VISIBILITY,
        )
        .order_by(ConsentRecord.created_at.desc(), ConsentRecord.id.desc())
        .first()
    )
    return bool(row and row.granted)


def _profile_response(profile: Profile | None) -> MatchingProfileResponse:
    return MatchingProfileResponse(
        course=profile.course if profile else None,
        year=profile.year if profile else None,
        interests=profile.interests or [] if profile else [],
        activity_types=profile.activity_types or [] if profile else [],
        region=profile.region if profile else None,
        language=profile.language if profile else None,
    )


def _candidate(user: User, profile: Profile) -> MatchingCandidateInternal:
    return MatchingCandidateInternal(
        user_id=user.id,
        display_name=user.pseudonymous_display_name,
        course=profile.course,
        year=profile.year,
        interests=profile.interests or [],
        activity_types=profile.activity_types or [],
        region=profile.region,
        language=profile.language,
    )


@router.get("/users/{user_id}/matching-profile", response_model=MatchingProfileResponse)
def get_matching_profile(user_id: uuid.UUID, db: Session = Depends(get_db)) -> MatchingProfileResponse:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    return _profile_response(profile)


@router.put("/users/{user_id}/matching-profile", response_model=MatchingProfileResponse)
def update_matching_profile(
    user_id: uuid.UUID, payload: MatchingProfileRequest, db: Session = Depends(get_db)
) -> MatchingProfileResponse:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if profile is None:
        profile = Profile(user_id=user_id)
        db.add(profile)
    profile.course = payload.course
    profile.year = payload.year
    profile.interests = payload.interests
    profile.activity_types = [item.value for item in payload.activity_types]
    profile.region = payload.region
    profile.language = payload.language
    db.commit()
    db.refresh(profile)
    return _profile_response(profile)


@router.get("/matching/candidates/{user_id}", response_model=MatchingCandidatePoolResponse)
def matching_candidate_pool(
    user_id: uuid.UUID, db: Session = Depends(get_db)
) -> MatchingCandidatePoolResponse:
    """Return only opted-in candidate data to matching-service, never a browser.

    This endpoint protects the source data boundary.  Block/report exclusion
    happens in matching-service's SQL query, after this narrow candidate pool
    is received, because those safety records are owned by matching-service.
    """
    requester = db.get(User, user_id)
    requester_profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    requester_settings = db.query(PrivacySettings).filter(PrivacySettings.user_id == user_id).first()
    if (
        requester is None
        or requester_profile is None
        or not requester.age_verified
        or requester_settings is None
        or not requester_settings.profile_visible_in_matching
        or not _latest_matching_consent_is_granted(db, user_id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Matching requires an age-verified, opted-in visible profile.",
        )

    rows = (
        db.query(User, Profile)
        .join(Profile, Profile.user_id == User.id)
        .join(PrivacySettings, PrivacySettings.user_id == User.id)
        .filter(
            User.id != user_id,
            User.age_verified.is_(True),
            PrivacySettings.profile_visible_in_matching.is_(True),
        )
        .all()
    )
    candidates = [
        _candidate(user, profile)
        for user, profile in rows
        if _latest_matching_consent_is_granted(db, user.id)
    ]
    return MatchingCandidatePoolResponse(
        requester=_candidate(requester, requester_profile), candidates=candidates
    )

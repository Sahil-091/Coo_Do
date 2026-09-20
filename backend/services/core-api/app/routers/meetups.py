"""Phase 13 public-venue meetups. No user coordinates are stored or returned."""
import math
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.schemas import (
    ActivityMeetupCreateRequest,
    ActivityMeetupResponse,
    ActivityRSVPRequest,
    AreaPreferenceRequest,
    AreaPreferenceResponse,
    VenueResponse,
)
from app.security import verify_internal_secret
from db.models.core import (
    ActivityAlertPreference,
    ActivityMeetup,
    ActivityRSVP,
    ConsentRecord,
    ConsentType,
    MeetupStatus,
    Profile,
    RSVPStatus,
    User,
)

router = APIRouter(prefix="/internal/users", tags=["meetups"], dependencies=[Depends(verify_internal_secret)])

# Phase 12 allows a new account one anonymous room per day. A real-world
# invitation reaches strangers at a physical venue, so its initial limit is
# deliberately stricter: one activity in seven days.
NEW_ACCOUNT_WINDOW = timedelta(days=30)
NEW_ACCOUNT_CREATION_WINDOW = timedelta(days=7)
NEW_ACCOUNT_CREATION_LIMIT = 1
ESTABLISHED_ACCOUNT_CREATION_WINDOW = timedelta(days=1)
ESTABLISHED_ACCOUNT_CREATION_LIMIT = 3

# Replaceable server-owned places adapter. IDs, names, and map URLs are never
# accepted from a browser, so an address cannot be smuggled through creation.
PUBLIC_VENUES = {
    "demo-central-library": ("Central Library", "library", "area:190:772", "https://maps.google.com/?q=Central+Library"),
    "demo-campus-sports-complex": ("Campus Sports Complex", "sports", "area:190:772", "https://maps.google.com/?q=Campus+Sports+Complex"),
    "demo-city-park": ("City Public Park", "park", "area:190:772", "https://maps.google.com/?q=City+Public+Park"),
}

# Profile tags are intentionally evaluated only inside core-api. They decide
# who may receive a notification, never what another member can browse.
CATEGORY_TERMS = {
    "cricket": {"cricket"},
    "football": {"football", "soccer"},
    "study_group": {"study", "study group", "studying"},
    "coding": {"coding", "programming", "technology"},
    "coffee_chat": {"coffee", "coffee chat", "conversation"},
    "walk": {"walk", "walking", "outdoors"},
    "gym": {"gym", "fitness", "workout"},
}


def _cell(latitude: float, longitude: float) -> str:
    # 0.1° cells are deliberately neighbourhood/district-scale. The raw input
    # is used only for this calculation and is never logged or persisted.
    return f"area:{math.floor((latitude + 90) * 10)}:{math.floor((longitude + 180) * 10)}"


def _consent_granted(db: Session, user_id: uuid.UUID) -> bool:
    row = db.query(ConsentRecord).filter(ConsentRecord.user_id == user_id, ConsentRecord.consent_type == ConsentType.ACTIVITY_ALERTS).order_by(ConsentRecord.created_at.desc()).first()
    return bool(row and row.granted)


def _profile_matches_category(profile: Profile | None, category: str) -> bool:
    if profile is None:
        return False
    selected = {
        str(value).strip().lower()
        for value in (profile.interests or []) + (profile.activity_types or [])
    }
    return bool(selected & CATEGORY_TERMS[category])


def _screen_or_reject(user_id: uuid.UUID, title: str, description: str) -> None:
    try:
        response = httpx.post(f"{settings.moderation_service_internal_url}/internal/moderation/screen", headers={"X-Internal-Secret": settings.internal_shared_secret}, json={"user_id": str(user_id), "text": f"{title}\n{description}", "source": "activity_meetup"}, timeout=12.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Activity screening is temporarily unavailable") from exc
    if response.json().get("held", True):
        raise HTTPException(status_code=422, detail="This activity needs moderator review before it can be published.")


def _response(db: Session, item: ActivityMeetup, user_id: uuid.UUID) -> ActivityMeetupResponse:
    joining = db.query(func.count(ActivityRSVP.id)).filter(ActivityRSVP.activity_meetup_id == item.id, ActivityRSVP.status == RSVPStatus.JOINING).scalar() or 0
    maybe = db.query(func.count(ActivityRSVP.id)).filter(ActivityRSVP.activity_meetup_id == item.id, ActivityRSVP.status == RSVPStatus.MAYBE).scalar() or 0
    mine = db.query(ActivityRSVP).filter(ActivityRSVP.activity_meetup_id == item.id, ActivityRSVP.user_id == user_id).one_or_none()
    return ActivityMeetupResponse(id=item.id, title=item.title, description=item.description, category=item.category, venue_name=item.venue_name, venue_map_url=item.venue_map_url, starts_at=item.starts_at, max_participants=item.max_participants, joining_count=joining, maybe_count=maybe, my_rsvp=mine.status if mine else None)


def _notify_eligible_users(db: Session, item: ActivityMeetup) -> None:
    # This is a core-api-only query over its own data. notification-service
    # receives only already-authorized recipient ids and no location/profile
    # data, so this is not a cross-service database join.
    candidates = (
        db.query(ActivityAlertPreference, Profile)
        .outerjoin(Profile, Profile.user_id == ActivityAlertPreference.user_id)
        .filter(
            ActivityAlertPreference.enabled.is_(True),
            ActivityAlertPreference.area_cell == item.area_cell,
            ActivityAlertPreference.user_id != item.creator_user_id,
        )
        .all()
    )
    recipient_ids = [
        preference.user_id
        for preference, profile in candidates
        if _consent_granted(db, preference.user_id)
        and _profile_matches_category(profile, item.category.value)
    ]
    if not recipient_ids:
        return
    try:
        httpx.post(f"{settings.notification_service_internal_url}/internal/activity-alerts", headers={"X-Internal-Secret": settings.internal_shared_secret}, json={"recipient_ids": [str(item) for item in recipient_ids], "meetup_id": str(item.id), "category": item.category.value}, timeout=5.0).raise_for_status()
    except httpx.HTTPError:
        # Publishing remains safe if delivery is delayed; production needs an
        # outbox/retry adapter before launch, recorded in the Phase 13 gate.
        return


@router.get("/{user_id}/meetup-venues", response_model=list[VenueResponse])
def venues(user_id: uuid.UUID, query: str = Query(default="", max_length=80), db: Session = Depends(get_db)):
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found.")
    needle = query.lower().strip()
    return [VenueResponse(id=key, name=value[0], category=value[1], map_url=value[3]) for key, value in PUBLIC_VENUES.items() if not needle or needle in value[0].lower()]


@router.put("/{user_id}/activity-alert-preference", response_model=AreaPreferenceResponse)
def set_alert_area(user_id: uuid.UUID, payload: AreaPreferenceRequest, db: Session = Depends(get_db)):
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found.")
    preference = db.query(ActivityAlertPreference).filter(ActivityAlertPreference.user_id == user_id).one_or_none()
    if not payload.enabled:
        # A user can clear their opt-in area without sending location again.
        # Removing the cell is data minimization, not merely a UI toggle.
        if preference is not None:
            db.delete(preference)
            db.commit()
        return AreaPreferenceResponse(enabled=False, has_area=False)
    if not _consent_granted(db, user_id):
        raise HTTPException(
            status_code=409,
            detail="Grant activity-alert consent before enabling area alerts.",
        )
    assert payload.latitude is not None and payload.longitude is not None
    if preference is None:
        preference = ActivityAlertPreference(
            user_id=user_id,
            area_cell=_cell(payload.latitude, payload.longitude),
            enabled=payload.enabled,
        )
        db.add(preference)
    else:
        preference.area_cell = _cell(payload.latitude, payload.longitude)
        preference.enabled = payload.enabled
    db.commit()
    return AreaPreferenceResponse(enabled=preference.enabled, has_area=True)


@router.get("/{user_id}/meetups", response_model=list[ActivityMeetupResponse])
def list_meetups(user_id: uuid.UUID, db: Session = Depends(get_db)):
    preference = db.query(ActivityAlertPreference).filter(ActivityAlertPreference.user_id == user_id, ActivityAlertPreference.enabled.is_(True)).one_or_none()
    if preference is None:
        return []
    rows = db.query(ActivityMeetup).filter(ActivityMeetup.status == MeetupStatus.PUBLISHED, ActivityMeetup.area_cell == preference.area_cell, ActivityMeetup.starts_at >= datetime.now(UTC)).order_by(ActivityMeetup.starts_at).all()
    return [_response(db, item, user_id) for item in rows]


@router.post("/{user_id}/meetups", response_model=ActivityMeetupResponse, status_code=status.HTTP_201_CREATED)
def create_meetup(user_id: uuid.UUID, payload: ActivityMeetupCreateRequest, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if payload.venue_id not in PUBLIC_VENUES:
        raise HTTPException(
            status_code=422,
            detail="Choose a verified public venue from the venue lookup.",
        )
    if payload.starts_at <= datetime.now(UTC) + timedelta(minutes=30):
        raise HTTPException(
            status_code=422,
            detail="Choose a start time at least 30 minutes from now.",
        )
    is_new = datetime.now(UTC) - user.created_at < NEW_ACCOUNT_WINDOW
    limit = NEW_ACCOUNT_CREATION_LIMIT if is_new else ESTABLISHED_ACCOUNT_CREATION_LIMIT
    creation_window = NEW_ACCOUNT_CREATION_WINDOW if is_new else ESTABLISHED_ACCOUNT_CREATION_WINDOW
    recent = db.query(ActivityMeetup).filter(ActivityMeetup.creator_user_id == user_id, ActivityMeetup.created_at >= datetime.now(UTC) - creation_window).count()
    if recent >= limit:
        raise HTTPException(
            status_code=429,
            detail="Activity creation limit reached. Try again tomorrow.",
        )
    _screen_or_reject(user_id, payload.title, payload.description)
    name, _kind, area_cell, map_url = PUBLIC_VENUES[payload.venue_id]
    item = ActivityMeetup(creator_user_id=user_id, title=payload.title.strip(), description=payload.description.strip(), category=payload.category, venue_provider_id=payload.venue_id, venue_name=name, venue_map_url=map_url, area_cell=area_cell, starts_at=payload.starts_at, max_participants=payload.max_participants)
    db.add(item)
    db.commit()
    db.refresh(item)
    _notify_eligible_users(db, item)
    return _response(db, item, user_id)


@router.put("/{user_id}/meetups/{meetup_id}/rsvp", response_model=ActivityMeetupResponse)
def rsvp(user_id: uuid.UUID, meetup_id: uuid.UUID, payload: ActivityRSVPRequest, db: Session = Depends(get_db)):
    # Lock the event row while we count and write. Without it, two concurrent
    # Join requests could both observe the final open seat and overbook it.
    item = db.query(ActivityMeetup).filter(ActivityMeetup.id == meetup_id).with_for_update().one_or_none()
    if item is None or item.status != MeetupStatus.PUBLISHED:
        raise HTTPException(status_code=404, detail="Activity not found.")
    current = db.query(ActivityRSVP).filter(ActivityRSVP.activity_meetup_id == meetup_id, ActivityRSVP.user_id == user_id).one_or_none()
    joining = db.query(ActivityRSVP).filter(ActivityRSVP.activity_meetup_id == meetup_id, ActivityRSVP.status == RSVPStatus.JOINING).count()
    if (
        payload.status == RSVPStatus.JOINING
        and (current is None or current.status != RSVPStatus.JOINING)
        and joining >= item.max_participants
    ):
        raise HTTPException(status_code=409, detail="This activity is full.")
    if current is None:
        db.add(ActivityRSVP(activity_meetup_id=meetup_id, user_id=user_id, status=payload.status))
    else:
        current.status = payload.status
    db.commit()
    return _response(db, item, user_id)

from datetime import UTC, datetime, timedelta

from app.routers import meetups
from app.routers.meetups import NEW_ACCOUNT_CREATION_LIMIT, NEW_ACCOUNT_CREATION_WINDOW
from fastapi import HTTPException

from db.base import SessionLocal
from db.models.core import (
    ActivityAlertPreference,
    ActivityMeetup,
    ConsentRecord,
    ConsentType,
    MeetupCategory,
    Profile,
    User,
)
from tests.conftest import INTERNAL_SECRET_HEADERS


def _allow_screen(_user_id, _title, _description):
    """Keep endpoint tests local; moderation's own suite covers screening."""


def _register(client, number: int) -> str:
    response = client.post(
        "/internal/auth/register",
        json={"email": f"meetup-{number}@example.com", "password": "correct-horse-battery-staple"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 201, response.text
    return response.json()["user_id"]


def _payload(**overrides):
    payload = {
        "title": "Library study circle",
        "description": "Bring your own notes and work alongside other students.",
        "category": "study_group",
        "venue_id": "demo-central-library",
        "starts_at": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
        "max_participants": 2,
    }
    payload.update(overrides)
    return payload


def _create(client, user_id: str, **overrides):
    return client.post(
        f"/internal/users/{user_id}/meetups",
        json=_payload(**overrides),
        headers=INTERNAL_SECRET_HEADERS,
    )


def test_creation_requires_a_server_catalogue_venue_and_never_accepts_address_fields(
    client, registered_user, monkeypatch
):
    monkeypatch.setattr(meetups, "_screen_or_reject", _allow_screen)
    user_id, _, _ = registered_user

    rejected = _create(
        client,
        user_id,
        address="12 Baker Street",
    )
    assert rejected.status_code == 422

    created = _create(client, user_id)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["venue_name"] == "Central Library"
    assert body["venue_map_url"].startswith("https://maps.google.com/")
    assert "creator_user_id" not in body
    assert "area_cell" not in body
    assert "participants" not in body


def test_area_coordinates_are_immediately_coarsened_and_clearable(client, registered_user):
    user_id, _, _ = registered_user
    consent = client.post(
        f"/internal/users/{user_id}/consents",
        json={"consent_type": "activity_alerts", "granted": True},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert consent.status_code == 201

    response = client.put(
        f"/internal/users/{user_id}/activity-alert-preference",
        json={"latitude": 12.9716, "longitude": 77.5946, "enabled": True},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == {"enabled": True, "has_area": True}
    assert "12.9716" not in response.text
    assert "77.5946" not in response.text

    with SessionLocal() as db:
        preference = db.query(ActivityAlertPreference).filter_by(user_id=user_id).one()
        assert preference.area_cell.startswith("area:")
        assert not hasattr(preference, "latitude")
        assert not hasattr(preference, "longitude")

    cleared = client.put(
        f"/internal/users/{user_id}/activity-alert-preference",
        json={"enabled": False},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert cleared.status_code == 200
    assert cleared.json() == {"enabled": False, "has_area": False}
    with SessionLocal() as db:
        assert db.query(ActivityAlertPreference).filter_by(user_id=user_id).count() == 0


def test_activity_screening_fails_closed_without_storing_or_publishing(client, registered_user, monkeypatch):
    monkeypatch.setattr(
        meetups,
        "_screen_or_reject",
        lambda *_args: (_ for _ in ()).throw(HTTPException(status_code=503)),
    )
    user_id, _, _ = registered_user
    response = _create(client, user_id)
    assert response.status_code == 503
    with SessionLocal() as db:
        assert db.query(ActivityMeetup).count() == 0


def test_new_accounts_have_a_stricter_activity_creation_limit(client, registered_user, monkeypatch):
    monkeypatch.setattr(meetups, "_screen_or_reject", _allow_screen)
    user_id, _, _ = registered_user
    assert NEW_ACCOUNT_CREATION_LIMIT == 1
    assert NEW_ACCOUNT_CREATION_WINDOW == timedelta(days=7)
    assert _create(client, user_id).status_code == 201
    assert _create(client, user_id, title="A second study circle").status_code == 429


def test_rsvp_states_expose_counts_but_never_members_and_enforce_capacity(client, registered_user, monkeypatch):
    monkeypatch.setattr(meetups, "_screen_or_reject", _allow_screen)
    creator, _, _ = registered_user
    activity = _create(client, creator).json()
    first = _register(client, 1)
    second = _register(client, 2)
    third = _register(client, 3)

    joining = client.put(
        f"/internal/users/{first}/meetups/{activity['id']}/rsvp",
        json={"status": "joining"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert joining.status_code == 200
    assert joining.json()["joining_count"] == 1
    maybe = client.put(
        f"/internal/users/{second}/meetups/{activity['id']}/rsvp",
        json={"status": "maybe"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert maybe.json()["maybe_count"] == 1
    assert client.put(
        f"/internal/users/{third}/meetups/{activity['id']}/rsvp",
        json={"status": "joining"},
        headers=INTERNAL_SECRET_HEADERS,
    ).status_code == 200
    full = _register(client, 4)
    assert client.put(
        f"/internal/users/{full}/meetups/{activity['id']}/rsvp",
        json={"status": "joining"},
        headers=INTERNAL_SECRET_HEADERS,
    ).status_code == 409
    assert "user_id" not in joining.json()
    assert "participants" not in joining.json()


def test_notification_filter_requires_consent_enabled_matching_area_and_interest(monkeypatch):
    captured: list[dict] = []

    class Response:
        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        meetups.httpx,
        "post",
        lambda _url, **kwargs: captured.append(kwargs["json"]) or Response(),
    )
    with SessionLocal() as db:
        creator = User(email="creator@example.com", password_hash="x")
        eligible = User(email="eligible@example.com", password_hash="x")
        wrong_interest = User(email="wrong-interest@example.com", password_hash="x")
        revoked = User(email="revoked@example.com", password_hash="x")
        other_area = User(email="other-area@example.com", password_hash="x")
        db.add_all([creator, eligible, wrong_interest, revoked, other_area])
        db.flush()
        db.add_all([
            Profile(user_id=eligible.id, interests=["coding"]),
            Profile(user_id=wrong_interest.id, interests=["football"]),
            Profile(user_id=revoked.id, interests=["coding"]),
            Profile(user_id=other_area.id, interests=["coding"]),
            ActivityAlertPreference(user_id=eligible.id, area_cell="area:190:772", enabled=True),
            ActivityAlertPreference(user_id=wrong_interest.id, area_cell="area:190:772", enabled=True),
            ActivityAlertPreference(user_id=revoked.id, area_cell="area:190:772", enabled=True),
            ActivityAlertPreference(user_id=other_area.id, area_cell="area:190:773", enabled=True),
            ConsentRecord(user_id=eligible.id, consent_type=ConsentType.ACTIVITY_ALERTS, granted=True),
            ConsentRecord(user_id=wrong_interest.id, consent_type=ConsentType.ACTIVITY_ALERTS, granted=True),
            ConsentRecord(user_id=revoked.id, consent_type=ConsentType.ACTIVITY_ALERTS, granted=False),
            ConsentRecord(user_id=other_area.id, consent_type=ConsentType.ACTIVITY_ALERTS, granted=True),
        ])
        activity = ActivityMeetup(
            creator_user_id=creator.id,
            title="Coding co-work",
            description="Bring a small project and work together.",
            category=MeetupCategory.CODING,
            venue_provider_id="demo-central-library",
            venue_name="Central Library",
            venue_map_url="https://maps.google.com/?q=Central+Library",
            area_cell="area:190:772",
            starts_at=datetime.now(UTC) + timedelta(hours=2),
            max_participants=8,
        )
        db.add(activity)
        db.flush()
        meetups._notify_eligible_users(db, activity)
        assert captured[0]["recipient_ids"] == [str(eligible.id)]
        assert "area_cell" not in captured[0]
        assert "interests" not in captured[0]

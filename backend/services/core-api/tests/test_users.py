import uuid
from datetime import date, timedelta

from tests.conftest import INTERNAL_SECRET_HEADERS


def _iso(d: date) -> str:
    return d.isoformat()


def test_age_verification_passes_for_18_plus(client, registered_user):
    user_id, _, _ = registered_user
    dob = date.today().replace(year=date.today().year - 20)
    response = client.put(
        f"/internal/users/{user_id}/age-verification",
        json={"date_of_birth": _iso(dob)},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 200, response.text
    assert response.json()["age_verified"] is True


def test_age_verification_fails_under_18(client, registered_user):
    user_id, _, _ = registered_user
    dob = date.today().replace(year=date.today().year - 15)
    response = client.put(
        f"/internal/users/{user_id}/age-verification",
        json={"date_of_birth": _iso(dob)},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["age_verified"] is False

    # Hard gate is server-side and persisted, not just a one-off response.
    state = client.get(f"/internal/users/{user_id}", headers=INTERNAL_SECRET_HEADERS)
    assert state.json()["age_verified"] is False


def test_age_verification_boundary_turns_18_today(client, registered_user):
    """Someone whose 18th birthday is exactly today should pass."""
    user_id, _, _ = registered_user
    today = date.today()
    dob = today.replace(year=today.year - 18)
    response = client.put(
        f"/internal/users/{user_id}/age-verification",
        json={"date_of_birth": _iso(dob)},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.json()["age_verified"] is True


def test_age_verification_boundary_turns_18_tomorrow_fails(client, registered_user):
    """One day short of 18 must still fail — off-by-one is exactly the bug to catch here."""
    user_id, _, _ = registered_user
    tomorrow = date.today() + timedelta(days=1)
    dob = tomorrow.replace(year=tomorrow.year - 18)
    response = client.put(
        f"/internal/users/{user_id}/age-verification",
        json={"date_of_birth": _iso(dob)},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.json()["age_verified"] is False


def test_age_verification_rejects_future_date(client, registered_user):
    user_id, _, _ = registered_user
    future = date.today() + timedelta(days=1)
    response = client.put(
        f"/internal/users/{user_id}/age-verification",
        json={"date_of_birth": _iso(future)},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 422


def test_unknown_user_returns_404(client):
    response = client.get(f"/internal/users/{uuid.uuid4()}", headers=INTERNAL_SECRET_HEADERS)
    assert response.status_code == 404


def test_display_name_can_be_set_and_cleared(client, registered_user):
    user_id, _, _ = registered_user

    set_response = client.put(
        f"/internal/users/{user_id}/display-name",
        json={"pseudonymous_display_name": "Quiet Fox"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert set_response.json()["pseudonymous_display_name"] == "Quiet Fox"

    clear_response = client.put(
        f"/internal/users/{user_id}/display-name",
        json={"pseudonymous_display_name": ""},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert clear_response.json()["pseudonymous_display_name"] is None


def test_consents_default_to_not_granted_for_all_known_types(client, registered_user):
    user_id, _, _ = registered_user
    response = client.get(f"/internal/users/{user_id}/consents", headers=INTERNAL_SECRET_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 4  # ai_chat, anonymous_community, matching_visibility, institutional_data_sharing
    assert all(item["granted"] is False for item in body)
    assert all(item["updated_at"] is None for item in body)


def test_granting_a_consent_reflects_in_latest_state(client, registered_user):
    user_id, _, _ = registered_user
    post_response = client.post(
        f"/internal/users/{user_id}/consents",
        json={"consent_type": "ai_chat", "granted": True},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert post_response.status_code == 201

    get_response = client.get(f"/internal/users/{user_id}/consents", headers=INTERNAL_SECRET_HEADERS)
    ai_chat_state = next(item for item in get_response.json() if item["consent_type"] == "ai_chat")
    assert ai_chat_state["granted"] is True
    assert ai_chat_state["updated_at"] is not None

    other_state = next(
        item for item in get_response.json() if item["consent_type"] == "anonymous_community"
    )
    assert other_state["granted"] is False


def test_consent_is_append_only_and_revocable(client, registered_user):
    """Granting then revoking should leave TWO rows in the audit trail,
    with GET reflecting only the latest (revoked) state."""
    user_id, _, _ = registered_user
    client.post(
        f"/internal/users/{user_id}/consents",
        json={"consent_type": "matching_visibility", "granted": True},
        headers=INTERNAL_SECRET_HEADERS,
    )
    client.post(
        f"/internal/users/{user_id}/consents",
        json={"consent_type": "matching_visibility", "granted": False},
        headers=INTERNAL_SECRET_HEADERS,
    )

    get_response = client.get(f"/internal/users/{user_id}/consents", headers=INTERNAL_SECRET_HEADERS)
    state = next(
        item for item in get_response.json() if item["consent_type"] == "matching_visibility"
    )
    assert state["granted"] is False


def test_privacy_settings_default_and_update(client, registered_user):
    user_id, _, _ = registered_user

    get_response = client.get(
        f"/internal/users/{user_id}/privacy-settings", headers=INTERNAL_SECRET_HEADERS
    )
    assert get_response.json()["profile_visible_in_matching"] is False
    assert get_response.json()["display_name_visible_in_rooms"] is False

    put_response = client.put(
        f"/internal/users/{user_id}/privacy-settings",
        json={"profile_visible_in_matching": True, "display_name_visible_in_rooms": False},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert put_response.status_code == 200
    assert put_response.json()["profile_visible_in_matching"] is True


def test_data_request_create_and_list(client, registered_user):
    user_id, _, _ = registered_user

    create_response = client.post(
        f"/internal/users/{user_id}/data-requests",
        json={"request_type": "export"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["status"] == "pending"
    assert body["completed_at"] is None

    list_response = client.get(
        f"/internal/users/{user_id}/data-requests", headers=INTERNAL_SECRET_HEADERS
    )
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["request_type"] == "export"


def test_data_requests_require_internal_secret(client, registered_user):
    user_id, _, _ = registered_user
    response = client.get(f"/internal/users/{user_id}/data-requests")
    assert response.status_code in (401, 422)

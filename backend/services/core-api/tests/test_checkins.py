from tests.conftest import INTERNAL_SECRET_HEADERS


def test_submit_checkin_persists_and_returns_routing(client, registered_user):
    user_id, _, _ = registered_user
    response = client.post(
        f"/internal/users/{user_id}/checkins",
        json={
            "feelings": ["lonely", "exhausted"],
            "stated_need": "relax",
            "time_of_day": "night",
        },
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 201, response.text
    body = response.json()

    assert body["checkin"]["feelings"] == ["lonely", "exhausted"]
    assert body["checkin"]["stated_need"] == "relax"
    assert body["checkin"]["id"]
    assert body["checkin"]["created_at"]

    # lonely + night + relax triggers the presence-mode modifier — this
    # is a real integration check that the API layer is actually calling
    # the rules engine, not just echoing input back.
    assert body["routing"]["path"] == "presence_mode"
    assert "lonely and exhausted" in body["routing"]["reason"]


def test_submit_checkin_ask_for_help_routes_to_professional_help(client, registered_user):
    user_id, _, _ = registered_user
    response = client.post(
        f"/internal/users/{user_id}/checkins",
        json={"feelings": ["sad"], "stated_need": "ask_for_help", "time_of_day": "afternoon"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["routing"]["path"] == "professional_help"


def test_submit_checkin_rejects_empty_feelings_list(client, registered_user):
    user_id, _, _ = registered_user
    response = client.post(
        f"/internal/users/{user_id}/checkins",
        json={"feelings": [], "stated_need": "relax", "time_of_day": "night"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 422


def test_submit_checkin_rejects_unknown_feeling_value(client, registered_user):
    user_id, _, _ = registered_user
    response = client.post(
        f"/internal/users/{user_id}/checkins",
        json={"feelings": ["furious"], "stated_need": "relax", "time_of_day": "night"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 422


def test_submit_checkin_rejects_unknown_need_value(client, registered_user):
    user_id, _, _ = registered_user
    response = client.post(
        f"/internal/users/{user_id}/checkins",
        json={"feelings": ["sad"], "stated_need": "world_domination", "time_of_day": "night"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 422


def test_submit_checkin_for_unknown_user_returns_404(client):
    import uuid

    response = client.post(
        f"/internal/users/{uuid.uuid4()}/checkins",
        json={"feelings": ["sad"], "stated_need": "relax", "time_of_day": "night"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 404


def test_submit_checkin_requires_internal_secret(client, registered_user):
    user_id, _, _ = registered_user
    response = client.post(
        f"/internal/users/{user_id}/checkins",
        json={"feelings": ["sad"], "stated_need": "relax", "time_of_day": "night"},
    )
    assert response.status_code in (401, 422)


def test_multiple_checkins_from_same_user_are_all_persisted(client, registered_user):
    """No uniqueness constraint should block repeated check-ins — this is
    meant to be used many times."""
    user_id, _, _ = registered_user
    for _ in range(3):
        response = client.post(
            f"/internal/users/{user_id}/checkins",
            json={"feelings": ["sad"], "stated_need": "relax", "time_of_day": "afternoon"},
            headers=INTERNAL_SECRET_HEADERS,
        )
        assert response.status_code == 201

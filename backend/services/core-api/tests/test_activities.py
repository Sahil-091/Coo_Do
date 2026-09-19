import uuid

from fastapi import WebSocketDisconnect

from app.routers.activities import MAX_CREATED_PER_HOUR, MAX_JOIN_TOKENS_PER_HOUR, presence_manager

from tests.conftest import INTERNAL_SECRET_HEADERS


def _activity(client, user_id, topic="study"):
    return client.post(
        f"/internal/users/{user_id}/activities",
        json={"topic": topic},
        headers=INTERNAL_SECRET_HEADERS,
    )


def _token(client, user_id, activity_id):
    return client.post(
        f"/internal/users/{user_id}/activities/{activity_id}/presence-token",
        headers=INTERNAL_SECRET_HEADERS,
    )


def test_virtual_activity_has_no_location_or_participant_list_and_creation_is_limited(client, registered_user):
    user_id, _, _ = registered_user
    created = _activity(client, user_id)
    assert created.status_code == 201, created.text
    payload = created.json()
    assert payload["topic"] == "study"
    assert payload["headcount"] == 0
    assert "location" not in payload
    assert "participants" not in payload

    for topic in ("coding", "reading"):
        assert _activity(client, user_id, topic).status_code == 201
    limited = _activity(client, user_id, "writing")
    assert MAX_CREATED_PER_HOUR == 3
    assert limited.status_code == 429


def test_presence_websocket_broadcasts_only_anonymous_headcount_and_feedback_is_owned(client, registered_user):
    user_id, _, _ = registered_user
    created = _activity(client, user_id).json()
    access = _token(client, user_id, created["id"])
    assert access.status_code == 200, access.text
    token = access.json()

    with client.websocket_connect(
        f"/internal/users/presence-rooms/{token['room_id']}/ws?token={token['websocket_token']}"
    ) as socket:
        event = socket.receive_json()
        assert event == {"type": "headcount", "count": 1}
        socket.send_text("this is ignored and does not create a chat")

    saved = client.put(
        f"/internal/users/{user_id}/activities/{created['id']}/presence-feedback",
        json={"feedback": "less_alone"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert saved.status_code == 204
    assert presence_manager.headcount(uuid.UUID(token["room_id"])) == 0


def test_presence_socket_rejects_unsigned_tokens(client, registered_user):
    user_id, _, _ = registered_user
    created = _activity(client, user_id).json()
    try:
        with client.websocket_connect(f"/internal/users/presence-rooms/{created['room_id']}/ws?token=nope"):
            raise AssertionError("unsigned socket must not open")
    except WebSocketDisconnect as exc:
        assert exc.code == 1008


def test_join_token_rate_limiter_rejects_spam():
    user_id = uuid.uuid4()
    assert all(presence_manager.allow_join_token(user_id) for _ in range(MAX_JOIN_TOKENS_PER_HOUR))
    assert presence_manager.allow_join_token(user_id) is False

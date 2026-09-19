from app.journal_crypto import build_journal_cipher
from cryptography.fernet import Fernet
from sqlalchemy import text

from db.base import engine
from tests.conftest import INTERNAL_SECRET_HEADERS


def _create_entry(client, user_id, body: str):
    return client.post(
        f"/internal/users/{user_id}/journal",
        json={"body": body},
        headers=INTERNAL_SECRET_HEADERS,
    )


def _second_user(client):
    response = client.post(
        "/internal/auth/register",
        json={"email": "another-student@example.com", "password": "correct-horse-battery-staple"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 201, response.text
    return response.json()["user_id"]


def test_entry_is_encrypted_at_rest_and_export_contains_only_its_owner(client, registered_user):
    user_id, _, _ = registered_user
    other_user_id = _second_user(client)
    private_body = "A private thought that must never be stored as plaintext."

    created = _create_entry(client, user_id, private_body)
    assert created.status_code == 201, created.text
    _create_entry(client, other_user_id, "Another student's reflection")

    with engine.connect() as connection:
        stored = connection.execute(
            text("SELECT encrypted_body, encryption_version FROM journal_entries WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).one()
    assert private_body not in stored.encrypted_body
    assert stored.encryption_version == "fernet-multikey-v1"

    exported = client.get(f"/internal/users/{user_id}/journal/export", headers=INTERNAL_SECRET_HEADERS)
    assert exported.status_code == 200, exported.text
    assert [entry["body"] for entry in exported.json()["entries"]] == [private_body]


def test_keyring_encrypts_with_newest_key_and_decrypts_retired_key():
    retired_key = Fernet.generate_key()
    newest_key = Fernet.generate_key()
    old_token = Fernet(retired_key).encrypt(b"older private reflection")

    cipher = build_journal_cipher(f"{newest_key.decode()},{retired_key.decode()}")
    assert cipher.decrypt(old_token) == b"older private reflection"
    new_token = cipher.encrypt(b"new private reflection")
    assert Fernet(newest_key).decrypt(new_token) == b"new private reflection"


def test_missing_or_invalid_keyring_is_rejected_without_a_fallback():
    for value in ("", "not-a-fernet-key"):
        try:
            build_journal_cipher(value)
        except ValueError:
            pass
        else:
            raise AssertionError("an invalid managed keyring must fail")


def test_delete_operations_cannot_touch_another_students_entries(client, registered_user):
    user_id, _, _ = registered_user
    other_user_id = _second_user(client)
    own_entry = _create_entry(client, user_id, "Mine").json()
    other_entry = _create_entry(client, other_user_id, "Theirs").json()

    denied = client.delete(
        f"/internal/users/{user_id}/journal/{other_entry['id']}",
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert denied.status_code == 404

    deleted = client.delete(
        f"/internal/users/{user_id}/journal/{own_entry['id']}",
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert deleted.status_code == 204
    _create_entry(client, user_id, "Mine again")
    assert client.delete(f"/internal/users/{user_id}/journal", headers=INTERNAL_SECRET_HEADERS).status_code == 204

    assert client.get(f"/internal/users/{user_id}/journal", headers=INTERNAL_SECRET_HEADERS).json() == []
    assert [entry["body"] for entry in client.get(f"/internal/users/{other_user_id}/journal", headers=INTERNAL_SECRET_HEADERS).json()] == ["Theirs"]


def test_comparisons_are_fixed_narratives_and_indicators_are_separate(client, registered_user):
    user_id, _, _ = registered_user
    _create_entry(client, user_id, "I started by taking a short walk.")
    _create_entry(client, user_id, "I later called a friend.")

    # A check-in that expressly asks for help is not itself a help-seeking
    # event. Only an intentional click on a Professional Help resource below
    # can increment that separate indicator.
    checkin = client.post(
        f"/internal/users/{user_id}/checkins",
        json={"feelings": ["sad"], "stated_need": "ask_for_help", "time_of_day": "afternoon"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert checkin.status_code == 201

    ladder = client.get(
        f"/internal/users/{user_id}/tiny-actions/suggestion", headers=INTERNAL_SECRET_HEADERS
    ).json()["ladder"]
    completed = client.post(
        f"/internal/users/{user_id}/action-attempts",
        json={"tiny_action_id": ladder[1]["id"], "status": "completed"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert completed.status_code == 201

    comparisons = client.get(f"/internal/users/{user_id}/journal/comparisons", headers=INTERNAL_SECRET_HEADERS)
    assert [row["window_days"] for row in comparisons.json()] == [7, 30, 90]
    assert all("score" not in row["narrative"].lower() for row in comparisons.json())

    indicators = client.get(f"/internal/users/{user_id}/real-life-indicators", headers=INTERNAL_SECRET_HEADERS).json()
    assert {row["key"] for row in indicators} == {"tiny_actions", "activities", "help_seeking"}
    assert all("score" not in row["sentence"].lower() for row in indicators)
    assert next(row for row in indicators if row["key"] == "tiny_actions")["sentence"] == "Tiny actions completed: 1."
    assert next(row for row in indicators if row["key"] == "activities")["sentence"] == "Virtual activities joined: 0."
    assert next(row for row in indicators if row["key"] == "help_seeking")["sentence"] == "Help-seeking actions taken: 0."


def test_opening_a_resource_creates_the_only_help_seeking_event(client, registered_user):
    user_id, _, _ = registered_user
    resource = client.post(
        "/internal/professional-resources",
        json={
            "resource_key": "campus-counselling", "region": "India", "category": "Campus counselling",
            "title": "Campus counselling", "summary": "A private first conversation with a counsellor.",
            "contact_label": "Call", "contact_value": "Call now", "contact_uri": "tel:14416",
            "booking_steps": [], "opening_lines": [],
        },
        headers=INTERNAL_SECRET_HEADERS,
    ).json()

    opened = client.post(
        f"/internal/users/{user_id}/professional-resources/{resource['id']}/open",
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert opened.status_code == 200
    assert opened.json() == {"destination": "tel:14416", "action_type": "call_resource"}

    indicators = client.get(f"/internal/users/{user_id}/real-life-indicators", headers=INTERNAL_SECRET_HEADERS).json()
    assert next(row for row in indicators if row["key"] == "help_seeking")["sentence"] == "Help-seeking actions taken: 1."

    # There is deliberately no generic event-writing route: a check-in tag
    # or a caller-supplied label must not manufacture help-seeking history.
    invalid = client.post(
        f"/internal/users/{user_id}/help-seeking-actions",
        json={"action_type": "checkin_tag"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert invalid.status_code == 404

from cryptography.fernet import Fernet
from sqlalchemy import text

from app.trusted_contact_crypto import build_trusted_contact_cipher
from db.base import engine
from tests.conftest import INTERNAL_SECRET_HEADERS


def _contact_payload(**overrides):
    payload = {
        "display_name": "Asha",
        "relationship": "friend",
        "channel": "sms",
        "contact_value": "+91 98765 43210",
        "allowed_scenarios": ["feeling_overwhelmed", "need_to_talk"],
    }
    payload.update(overrides)
    return payload


def _create(client, user_id, **overrides):
    return client.post(
        f"/internal/users/{user_id}/trusted-contacts",
        json=_contact_payload(**overrides),
        headers=INTERNAL_SECRET_HEADERS,
    )


def test_contact_details_are_encrypted_and_scoped_to_the_owner(client, registered_user):
    user_id, _, _ = registered_user
    created = _create(client, user_id)
    assert created.status_code == 201, created.text
    contact = created.json()
    assert contact["display_name"] == "Asha"
    assert contact["allowed_scenarios"] == ["feeling_overwhelmed", "need_to_talk"]
    assert "contact_value" not in contact

    with engine.connect() as connection:
        stored = connection.execute(
            text("SELECT encrypted_payload FROM trusted_contacts WHERE id = :id"), {"id": contact["id"]}
        ).scalar_one()
    assert "Asha" not in stored
    assert "98765" not in stored

    other = client.post(
        "/internal/auth/register",
        json={"email": "other@example.com", "password": "correct-horse-battery-staple"},
        headers=INTERNAL_SECRET_HEADERS,
    ).json()["user_id"]
    denied = client.post(
        f"/internal/users/{other}/trusted-contacts/{contact['id']}/outreach",
        json={"scenario": "feeling_overwhelmed"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert denied.status_code == 404
    assert client.delete(f"/internal/users/{other}/trusted-contacts/{contact['id']}", headers=INTERNAL_SECRET_HEADERS).status_code == 404


def test_outreach_requires_an_explicit_allowed_scenario_and_only_returns_a_composer_uri(client, registered_user):
    user_id, _, _ = registered_user
    contact = _create(client, user_id).json()
    forbidden = client.post(
        f"/internal/users/{user_id}/trusted-contacts/{contact['id']}/outreach",
        json={"scenario": "practical_support"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert forbidden.status_code == 403

    prepared = client.post(
        f"/internal/users/{user_id}/trusted-contacts/{contact['id']}/outreach",
        json={"scenario": "feeling_overwhelmed"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["contact_name"] == "Asha"
    assert prepared.json()["destination"].startswith("sms:+91%2098765%2043210?body=")
    # The API returns a native composer URI. It does not call an SMS/email
    # provider or create an automatic notification record.
    assert "message" not in prepared.json()


def test_contact_keyring_encrypts_with_newest_key_and_rejects_missing_keyring():
    retired_key, newest_key = Fernet.generate_key(), Fernet.generate_key()
    cipher = build_trusted_contact_cipher(f"{newest_key.decode()},{retired_key.decode()}")
    old_token = Fernet(retired_key).encrypt(b"trusted contact")
    assert cipher.decrypt(old_token) == b"trusted contact"
    assert Fernet(newest_key).decrypt(cipher.encrypt(b"new contact")) == b"new contact"
    try:
        build_trusted_contact_cipher("")
    except ValueError:
        pass
    else:
        raise AssertionError("a missing trusted-contact keyring must fail")

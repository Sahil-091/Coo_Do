import os

from cryptography.fernet import Fernet

# Must happen before any import that transitively imports db.base, so the
# engine binds to core-api's OWN least-privilege role — not a superuser
# connection — matching how this service actually runs in production.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg2://app_core_api:change_me_core_api@localhost/campus_connect"
)
# A fresh key exists only in this test process.  Production has no fallback:
# its managed JOURNAL_ENCRYPTION_KEYS secret is required at application start.
os.environ.setdefault("JOURNAL_ENCRYPTION_KEYS", Fernet.generate_key().decode())
os.environ.setdefault("TRUSTED_CONTACT_ENCRYPTION_KEYS", Fernet.generate_key().decode())

import pytest
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import text

from db.base import engine

INTERNAL_SECRET_HEADERS = {"X-Internal-Secret": "dev-only-change-me"}


@pytest.fixture(autouse=True)
def clean_tables():
    """Full isolation between tests — delete in FK-safe (children-first) order."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM activity_rsvps"))
        conn.execute(text("DELETE FROM activity_meetups"))
        conn.execute(text("DELETE FROM activity_alert_preferences"))
        conn.execute(text("DELETE FROM trusted_contacts"))
        conn.execute(text("DELETE FROM activity_participants"))
        conn.execute(text("DELETE FROM presence_rooms"))
        conn.execute(text("DELETE FROM activities"))
        conn.execute(text("DELETE FROM help_seeking_actions"))
        conn.execute(text("DELETE FROM journal_entries"))
        conn.execute(text("DELETE FROM professional_resources"))
        conn.execute(text("DELETE FROM tiny_action_voice_events"))
        conn.execute(text("DELETE FROM data_requests"))
        conn.execute(text("DELETE FROM consent_records"))
        conn.execute(text("DELETE FROM privacy_settings"))
        conn.execute(text("DELETE FROM action_attempts"))
        conn.execute(text("DELETE FROM checkins"))
        conn.execute(text("DELETE FROM profiles"))
        conn.execute(text("DELETE FROM users"))
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    """Registers a fresh user and returns (user_id, email, password)."""
    email = "student@example.com"
    password = "correct-horse-battery-staple"
    response = client.post(
        "/internal/auth/register",
        json={"email": email, "password": password},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 201, response.text
    return response.json()["user_id"], email, password

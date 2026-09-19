from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "notification-service"


def test_activity_alert_endpoint_requires_internal_auth_and_deduplicates_recipients():
    import uuid

    recipient = str(uuid.uuid4())
    denied = client.post(
        "/internal/activity-alerts",
        json={"recipient_ids": [recipient], "meetup_id": str(uuid.uuid4()), "category": "coding"},
    )
    assert denied.status_code == 401
    accepted = client.post(
        "/internal/activity-alerts",
        headers={"X-Internal-Secret": "dev-only-change-me"},
        json={"recipient_ids": [recipient, recipient], "meetup_id": str(uuid.uuid4()), "category": "coding"},
    )
    assert accepted.status_code == 202
    assert accepted.json() == {"accepted": 1}

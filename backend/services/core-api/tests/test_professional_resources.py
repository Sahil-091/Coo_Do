from tests.conftest import INTERNAL_SECRET_HEADERS


def resource_payload(**overrides):
    payload = {
        "resource_key": "campus-wellbeing", "region": "India", "category": "Campus counselling",
        "title": "Campus wellbeing centre", "summary": "A private first conversation with a campus counsellor.",
        "contact_label": "Book online", "contact_value": "Book an appointment", "contact_uri": "https://campus.example/book",
        "booking_steps": ["Open the booking page.", "Choose a first appointment."],
        "what_to_expect": "You can begin with what has been hardest recently.",
        "opening_lines": ["I would like to talk to someone about how I have been feeling."],
        "last_verified_at": "2026-09-19",
    }
    payload.update(overrides)
    return payload


def test_directory_returns_only_active_entries_and_replacement_is_versioned(client):
    created = client.post("/internal/professional-resources", json=resource_payload(), headers=INTERNAL_SECRET_HEADERS)
    assert created.status_code == 201, created.text
    original = created.json()

    replacement = client.put(
        f"/internal/professional-resources/{original['id']}",
        json=resource_payload(title="Updated campus wellbeing centre"), headers=INTERNAL_SECRET_HEADERS,
    )
    assert replacement.status_code == 200, replacement.text
    assert replacement.json()["version"] == 2
    assert replacement.json()["title"] == "Updated campus wellbeing centre"

    active = client.get("/internal/professional-resources?region=India", headers=INTERNAL_SECRET_HEADERS)
    assert active.status_code == 200
    assert [row["id"] for row in active.json()] == [replacement.json()["id"]]

    audit = client.get("/internal/professional-resources?region=India&include_inactive=true", headers=INTERNAL_SECRET_HEADERS)
    assert len(audit.json()) == 2
    assert {row["version"] for row in audit.json()} == {1, 2}


def test_directory_rejects_duplicate_key_and_requires_internal_secret(client):
    assert client.post("/internal/professional-resources", json=resource_payload()).status_code in (401, 422)
    assert client.post("/internal/professional-resources", json=resource_payload(), headers=INTERNAL_SECRET_HEADERS).status_code == 201
    duplicate = client.post("/internal/professional-resources", json=resource_payload(), headers=INTERNAL_SECRET_HEADERS)
    assert duplicate.status_code == 409

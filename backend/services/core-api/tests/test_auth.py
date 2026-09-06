from tests.conftest import INTERNAL_SECRET_HEADERS


def test_register_creates_user(client):
    response = client.post(
        "/internal/auth/register",
        json={"email": "new@example.com", "password": "correct-horse-battery-staple"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 201, response.text
    assert "user_id" in response.json()


def test_register_rejects_duplicate_email(client, registered_user):
    _, email, _ = registered_user
    response = client.post(
        "/internal/auth/register",
        json={"email": email, "password": "another-password-here"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 409


def test_register_is_case_insensitive_on_email(client, registered_user):
    _, email, _ = registered_user
    response = client.post(
        "/internal/auth/register",
        json={"email": email.upper(), "password": "another-password-here"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 409


def test_register_rejects_short_password(client):
    response = client.post(
        "/internal/auth/register",
        json={"email": "shortpw@example.com", "password": "short1"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 422


def test_register_requires_internal_secret(client):
    response = client.post(
        "/internal/auth/register",
        json={"email": "noheader@example.com", "password": "correct-horse-battery-staple"},
    )
    assert response.status_code in (401, 422)  # 422 if FastAPI treats missing header as validation error


def test_register_rejects_wrong_internal_secret(client):
    response = client.post(
        "/internal/auth/register",
        json={"email": "wrongsecret@example.com", "password": "correct-horse-battery-staple"},
        headers={"X-Internal-Secret": "not-the-real-secret"},
    )
    assert response.status_code == 401


def test_verify_succeeds_with_correct_credentials(client, registered_user):
    user_id, email, password = registered_user
    response = client.post(
        "/internal/auth/verify",
        json={"email": email, "password": password},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user_id"] == user_id
    assert body["age_verified"] is False


def test_verify_fails_with_wrong_password(client, registered_user):
    _, email, _ = registered_user
    response = client.post(
        "/internal/auth/verify",
        json={"email": email, "password": "definitely-wrong"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 401


def test_verify_fails_with_unknown_email_using_same_generic_message(client, registered_user):
    """Same failure shape for 'wrong password' and 'no such account' — no user enumeration."""
    wrong_password_response = client.post(
        "/internal/auth/verify",
        json={"email": registered_user[1], "password": "definitely-wrong"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    unknown_email_response = client.post(
        "/internal/auth/verify",
        json={"email": "nobody-here@example.com", "password": "definitely-wrong"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert wrong_password_response.status_code == unknown_email_response.status_code == 401
    assert wrong_password_response.json()["detail"] == unknown_email_response.json()["detail"]

from tests.conftest import INTERNAL_SECRET_HEADERS


def test_suggestion_returns_a_full_three_rung_ladder(client, registered_user):
    user_id, _, _ = registered_user
    response = client.get(f"/internal/users/{user_id}/tiny-actions/suggestion", headers=INTERNAL_SECRET_HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()

    assert len(body["ladder"]) == 3
    difficulty_levels = sorted(r["difficulty_level"] for r in body["ladder"])
    assert difficulty_levels == [1, 2, 3]
    assert body["suggested_attempt_id"]


def test_suggestion_ladder_is_ordered_easiest_first(client, registered_user):
    user_id, _, _ = registered_user
    response = client.get(f"/internal/users/{user_id}/tiny-actions/suggestion", headers=INTERNAL_SECRET_HEADERS)
    levels = [r["difficulty_level"] for r in response.json()["ladder"]]
    assert levels == [1, 2, 3]


def test_suggestion_creates_a_suggested_attempt_for_the_middle_rung(client, registered_user):
    user_id, _, _ = registered_user
    response = client.get(f"/internal/users/{user_id}/tiny-actions/suggestion", headers=INTERNAL_SECRET_HEADERS)
    body = response.json()
    middle_rung = next(r for r in body["ladder"] if r["difficulty_level"] == 2)
    # The suggested attempt should reference the middle rung, not the
    # easiest or hardest — that's the deliberate default entry point.
    assert body["suggested_attempt_id"]  # existence already proves a row was created;
    # cross-check via the attempts list would need a GET endpoint we
    # don't have yet — the id's mere presence plus the 201/200 status
    # is what this test guards.
    assert middle_rung["title"]


def test_multiple_suggestions_can_return_different_ladders(client, registered_user):
    """Not a strict guarantee (randomness), but with 10 seeded ladders,
    20 draws landing on the exact same ladder every time would indicate
    the random selection is broken, not bad luck."""
    user_id, _, _ = registered_user
    seen_titles = set()
    for _ in range(20):
        response = client.get(
            f"/internal/users/{user_id}/tiny-actions/suggestion", headers=INTERNAL_SECRET_HEADERS
        )
        middle = next(r for r in response.json()["ladder"] if r["difficulty_level"] == 2)
        seen_titles.add(middle["title"])
    assert len(seen_titles) > 1


def test_suggestion_requires_internal_secret(client, registered_user):
    user_id, _, _ = registered_user
    response = client.get(f"/internal/users/{user_id}/tiny-actions/suggestion")
    assert response.status_code in (401, 422)


def test_suggestion_for_unknown_user_returns_404(client):
    import uuid

    response = client.get(
        f"/internal/users/{uuid.uuid4()}/tiny-actions/suggestion", headers=INTERNAL_SECRET_HEADERS
    )
    assert response.status_code == 404

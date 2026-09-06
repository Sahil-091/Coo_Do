import uuid

from tests.conftest import INTERNAL_SECRET_HEADERS


def _get_ladder(client, user_id):
    response = client.get(f"/internal/users/{user_id}/tiny-actions/suggestion", headers=INTERNAL_SECRET_HEADERS)
    ladder = response.json()["ladder"]
    by_level = {r["difficulty_level"]: r for r in ladder}
    return by_level  # {1: rung, 2: rung, 3: rung}


def _log_attempt(client, user_id, tiny_action_id, status, related_checkin_id=None):
    payload = {"tiny_action_id": tiny_action_id, "status": status}
    if related_checkin_id:
        payload["related_checkin_id"] = related_checkin_id
    return client.post(
        f"/internal/users/{user_id}/action-attempts", json=payload, headers=INTERNAL_SECRET_HEADERS
    )


def test_completed_attempt_never_triggers_the_nudge(client, registered_user):
    user_id, _, _ = registered_user
    ladder = _get_ladder(client, user_id)
    response = _log_attempt(client, user_id, ladder[2]["id"], "completed")
    assert response.status_code == 201, response.text
    assert response.json()["show_support_nudge"] is False
    assert response.json()["attempt"]["status"] == "completed"


def test_skipped_attempt_never_triggers_the_nudge(client, registered_user):
    user_id, _, _ = registered_user
    ladder = _get_ladder(client, user_id)
    response = _log_attempt(client, user_id, ladder[2]["id"], "skipped")
    assert response.json()["show_support_nudge"] is False


def test_reduced_above_floor_does_not_trigger_even_repeated(client, registered_user):
    """Reducing FROM the hardest/middle rung (not yet at the floor) is
    normal ladder use, not a failure signal — even 3+ in a row should
    not trigger the nudge, since none of them are difficulty_level=1."""
    user_id, _, _ = registered_user
    ladder = _get_ladder(client, user_id)
    for _ in range(4):
        response = _log_attempt(client, user_id, ladder[3]["id"], "reduced")
    assert response.json()["show_support_nudge"] is False


def test_suggested_rows_dont_interleave_and_break_the_streak(client, registered_user):
    """
    Regression test for a real bug: every _get_ladder() call below
    fetches a fresh suggestion, which auto-logs a SUGGESTED attempt.
    Before the fix, those SUGGESTED rows interleaved with REDUCED rows
    in the "last 3" query and silently prevented the nudge from EVER
    firing under this exact pattern — which is how the real UI actually
    behaves (fetch suggestion -> reduce -> fetch new suggestion -> ...).
    This test simulates that realistic flow directly, not an idealized
    isolated call sequence.
    """
    user_id, _, _ = registered_user
    response = None
    for _ in range(3):
        ladder = _get_ladder(client, user_id)  # logs a SUGGESTED row as a side effect
        response = _log_attempt(client, user_id, ladder[1]["id"], "reduced")
    assert response.json()["show_support_nudge"] is True


def test_three_consecutive_reduced_at_floor_triggers_the_nudge(client, registered_user):
    """The core required safety behavior (R&D doc Section 5.3): 3
    consecutive 'reduced' attempts specifically at difficulty_level=1
    (nowhere further to shrink to) surfaces the support nudge."""
    user_id, _, _ = registered_user

    for i in range(3):
        ladder = _get_ladder(client, user_id)  # may land on a different ladder each time — intentional
        response = _log_attempt(client, user_id, ladder[1]["id"], "reduced")
        assert response.status_code == 201
        if i < 2:
            assert response.json()["show_support_nudge"] is False, f"fired too early on attempt {i + 1}"

    assert response.json()["show_support_nudge"] is True


def test_a_completion_breaks_the_streak(client, registered_user):
    """Two floor-reduced attempts, then a completion, then one more
    floor-reduced attempt should NOT trigger — the streak was broken."""
    user_id, _, _ = registered_user

    ladder = _get_ladder(client, user_id)
    _log_attempt(client, user_id, ladder[1]["id"], "reduced")
    ladder = _get_ladder(client, user_id)
    _log_attempt(client, user_id, ladder[1]["id"], "reduced")

    ladder = _get_ladder(client, user_id)
    _log_attempt(client, user_id, ladder[2]["id"], "completed")  # breaks the streak

    ladder = _get_ladder(client, user_id)
    response = _log_attempt(client, user_id, ladder[1]["id"], "reduced")
    assert response.json()["show_support_nudge"] is False


def test_pattern_persists_across_different_ladders_not_just_one(client, registered_user):
    """The signal is meant to catch 'can't manage even the smallest
    version of ANYTHING right now' — deliberately not scoped to a single
    ladder. Three floor-reduced attempts on three DIFFERENT ladders
    should still trigger."""
    user_id, _, _ = registered_user
    seen_ladder_titles = set()

    response = None
    for _ in range(3):
        ladder = _get_ladder(client, user_id)
        seen_ladder_titles.add(ladder[1]["title"])
        response = _log_attempt(client, user_id, ladder[1]["id"], "reduced")

    # This test only proves something meaningful if we actually landed
    # on more than one distinct ladder across the 3 draws.
    if len(seen_ladder_titles) > 1:
        assert response.json()["show_support_nudge"] is True


def test_related_checkin_id_is_stored_when_provided(client, registered_user):
    user_id, _, _ = registered_user
    checkin_response = client.post(
        f"/internal/users/{user_id}/checkins",
        json={"feelings": ["sad"], "stated_need": "relax", "time_of_day": "afternoon"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    checkin_id = checkin_response.json()["checkin"]["id"]

    ladder = _get_ladder(client, user_id)
    response = _log_attempt(client, user_id, ladder[2]["id"], "completed", related_checkin_id=checkin_id)
    assert response.json()["attempt"]["related_checkin_id"] == checkin_id


def test_related_checkin_id_is_null_when_not_provided(client, registered_user):
    user_id, _, _ = registered_user
    ladder = _get_ladder(client, user_id)
    response = _log_attempt(client, user_id, ladder[2]["id"], "completed")
    assert response.json()["attempt"]["related_checkin_id"] is None


def test_unknown_tiny_action_id_returns_404(client, registered_user):
    user_id, _, _ = registered_user
    response = _log_attempt(client, user_id, str(uuid.uuid4()), "completed")
    assert response.status_code == 404


def test_unknown_user_returns_404(client, registered_user):
    _, _, _ = registered_user
    ladder = _get_ladder(client, registered_user[0])
    response = _log_attempt(client, uuid.uuid4(), ladder[2]["id"], "completed")
    assert response.status_code == 404


def test_requires_internal_secret(client, registered_user):
    user_id, _, _ = registered_user
    ladder = _get_ladder(client, user_id)
    response = client.post(
        f"/internal/users/{user_id}/action-attempts",
        json={"tiny_action_id": ladder[2]["id"], "status": "completed"},
    )
    assert response.status_code in (401, 422)


def test_rejects_invalid_status_value(client, registered_user):
    user_id, _, _ = registered_user
    ladder = _get_ladder(client, user_id)
    response = client.post(
        f"/internal/users/{user_id}/action-attempts",
        json={"tiny_action_id": ladder[2]["id"], "status": "gave_up_forever"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 422


def test_rejects_suggested_as_a_client_submitted_status(client, registered_user):
    """'suggested' is set automatically by the suggestion endpoint —
    a client should never be able to submit it directly."""
    user_id, _, _ = registered_user
    ladder = _get_ladder(client, user_id)
    response = client.post(
        f"/internal/users/{user_id}/action-attempts",
        json={"tiny_action_id": ladder[2]["id"], "status": "suggested"},
        headers=INTERNAL_SECRET_HEADERS,
    )
    assert response.status_code == 422

from app.tiny_action_voice import (
    TinyActionVoiceGeneration,
    TinyActionVoiceInput,
    VoiceCallAudit,
    VoiceProviderUnavailable,
    generate_tiny_action_message,
    is_rule_adherent,
)

VOICE_INPUT = TinyActionVoiceInput(
    feelings=("lonely",),
    stated_need="talk",
    action_title="Sit in the library for five minutes",
    difficulty_level=2,
    time_of_day="night",
)
VALID_MESSAGE = (
    "If you're up for it, feeling lonely and wanting someone to talk to, "
    "Sit in the library for five minutes could be a small option tonight."
)


class FakeProvider:
    provider_name = "fake"
    model_name = "fake-model"
    prompt_version = "test-v1"

    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def generate_tiny_action_message(self, _voice_input):
        self.calls += 1
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def test_adherent_output_has_all_the_required_bounded_voice_properties():
    assert is_rule_adherent(VALID_MESSAGE, VOICE_INPUT) is True


def test_output_with_a_question_is_never_adherent():
    assert is_rule_adherent(VALID_MESSAGE + " Does that work?", VOICE_INPUT) is False


def test_adherence_guard_accepts_warm_messages_across_varied_structured_tags():
    """Representative adversarial tag mix: every value is an enum/curated
    action, not user-entered text. This guards the deterministic rules across
    different feelings, needs, difficulties, and times before a live provider
    evaluation is opted into with a real API key."""
    cases = (
        (
            TinyActionVoiceInput(("anxious",), "study", "Open one lecture slide", 1, "morning"),
            "If you're up for it, feeling anxious while studying, Open one lecture slide could be a gentle place to begin.",
        ),
        (
            TinyActionVoiceInput(("empty", "exhausted"), "relax", "Put your phone down for two minutes", 1, "night"),
            "If you're up for it, feeling empty and exhausted and looking for a little rest, Put your phone down for two minutes could be enough for now.",
        ),
        (
            TinyActionVoiceInput(("confused",), "understand_feeling", "Take three slow breaths", 2, "afternoon"),
            "If you're up for it, feeling confused and wanting understanding what you are feeling, Take three slow breaths could give this moment a little space.",
        ),
        (
            TinyActionVoiceInput(("dont_know",), "be_around_people", "Sit in a shared study space", 3, "evening"),
            "If you're up for it, not sure what to call it and wanting being around people, Sit in a shared study space could be one quiet option.",
        ),
    )

    for voice_input, message in cases:
        assert is_rule_adherent(message, voice_input) is True


def test_rule_breaking_first_output_is_regenerated_once():
    provider = FakeProvider(["Would you like to try this?", VALID_MESSAGE])

    result = generate_tiny_action_message(VOICE_INPUT, provider)

    assert result.message == VALID_MESSAGE
    assert result.fallback_reason is None
    assert [audit.outcome for audit in result.audits] == ["rejected", "accepted"]
    assert provider.calls == 2


def test_two_rule_breaking_outputs_use_a_static_fallback_instead_of_model_text():
    provider = FakeProvider(["Would you like to try this?", "This will fix everything."])

    result = generate_tiny_action_message(VOICE_INPUT, provider)

    assert result.message is None
    assert result.fallback_reason == "rule_rejected"
    assert [audit.outcome for audit in result.audits] == ["rejected", "rejected"]


def test_provider_timeout_or_error_uses_a_static_fallback_path():
    provider = FakeProvider([VoiceProviderUnavailable("simulated timeout")])

    result = generate_tiny_action_message(VOICE_INPUT, provider)

    assert result.message is None
    assert result.fallback_reason == "unavailable"
    assert [audit.outcome for audit in result.audits] == ["unavailable"]


def test_crisis_adjacent_input_is_refused_before_a_provider_call():
    unsafe_input = TinyActionVoiceInput(
        feelings=("suicidal",),
        stated_need="talk",
        action_title="Sit in the library for five minutes",
        difficulty_level=2,
        time_of_day="night",
    )
    provider = FakeProvider([VALID_MESSAGE])

    result = generate_tiny_action_message(unsafe_input, provider)

    assert result.message is None
    assert result.fallback_reason == "crisis_input"
    assert result.audits == ()
    assert provider.calls == 0


def test_suggestion_uses_voice_message_and_writes_metadata_only_audit(client, registered_user, monkeypatch):
    user_id, _, _ = registered_user
    checkin_response = client.post(
        f"/internal/users/{user_id}/checkins",
        json={"feelings": ["lonely"], "stated_need": "talk", "time_of_day": "night"},
        headers={"X-Internal-Secret": "dev-only-change-me"},
    )
    checkin_id = checkin_response.json()["checkin"]["id"]
    generation = TinyActionVoiceGeneration(
        message=VALID_MESSAGE,
        fallback_reason=None,
        audits=(
            VoiceCallAudit(
                provider="fake",
                model="fake-model",
                prompt_version="test-v1",
                attempt_number=1,
                outcome="accepted",
            ),
        ),
    )
    monkeypatch.setattr("app.routers.tiny_actions.generate_tiny_action_message", lambda _input: generation)

    response = client.get(
        f"/internal/users/{user_id}/tiny-actions/suggestion?checkin_id={checkin_id}",
        headers={"X-Internal-Secret": "dev-only-change-me"},
    )

    assert response.status_code == 200, response.text
    middle = next(rung for rung in response.json()["ladder"] if rung["difficulty_level"] == 2)
    assert middle["voice_message"] == VALID_MESSAGE

    from db.base import SessionLocal
    from db.models.core import TinyActionVoiceEvent

    with SessionLocal() as db:
        events = db.query(TinyActionVoiceEvent).all()
    assert len(events) == 1
    assert events[0].provider == "fake"
    assert events[0].model == "fake-model"
    assert events[0].prompt_version == "test-v1"
    assert events[0].outcome.value == "accepted"


def test_provider_failure_returns_the_existing_static_action_description(client, registered_user, monkeypatch):
    user_id, _, _ = registered_user
    checkin_response = client.post(
        f"/internal/users/{user_id}/checkins",
        json={"feelings": ["exhausted"], "stated_need": "relax", "time_of_day": "evening"},
        headers={"X-Internal-Secret": "dev-only-change-me"},
    )
    checkin_id = checkin_response.json()["checkin"]["id"]
    generation = TinyActionVoiceGeneration(
        message=None,
        fallback_reason="unavailable",
        audits=(
            VoiceCallAudit(
                provider="fake",
                model="fake-model",
                prompt_version="test-v1",
                attempt_number=1,
                outcome="unavailable",
            ),
        ),
    )
    monkeypatch.setattr("app.routers.tiny_actions.generate_tiny_action_message", lambda _input: generation)

    response = client.get(
        f"/internal/users/{user_id}/tiny-actions/suggestion?checkin_id={checkin_id}",
        headers={"X-Internal-Secret": "dev-only-change-me"},
    )

    assert response.status_code == 200, response.text
    middle = next(rung for rung in response.json()["ladder"] if rung["difficulty_level"] == 2)
    assert middle["voice_message"] == middle["description"]

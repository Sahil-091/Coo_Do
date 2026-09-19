import pytest

from app.gemini_classifier import ClassifierUnavailable, parse_flag_level


@pytest.mark.parametrize("flag", ["none", "elevated", "crisis"])
def test_accepts_only_allowed_structured_flag_levels(flag: str):
    assert parse_flag_level(f'{{"flag_level":"{flag}"}}') == flag


@pytest.mark.parametrize("output", ["{}", '{"flag_level":"unknown"}', "not json"])
def test_invalid_provider_output_is_never_treated_as_safe(output: str):
    with pytest.raises(ClassifierUnavailable):
        parse_flag_level(output)

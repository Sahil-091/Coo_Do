import pytest
from app.checkin_rules import (
    Feeling,
    Need,
    SuggestedPath,
    TimeOfDay,
    route_checkin,
)

ALL_NEEDS = list(Need)
ALL_TIMES = list(TimeOfDay)


def test_every_need_produces_a_result_for_every_time_of_day():
    """Exhaustiveness check: no (need, time) combination should ever fall
    through to an unhandled state — every call must return a real path."""
    for need in ALL_NEEDS:
        for time_of_day in ALL_TIMES:
            result = route_checkin([Feeling.LONELY], need, time_of_day)
            assert result.path in list(SuggestedPath)
            assert result.reason  # never empty
            assert result.matched_rule_id != "fallback_default", (
                f"need={need}, time={time_of_day} hit the defensive fallback — "
                "every Need should be covered by an explicit rule"
            )


class TestAskForHelp:
    def test_always_routes_to_professional_help(self):
        result = route_checkin([Feeling.SAD], Need.ASK_FOR_HELP, TimeOfDay.MORNING)
        assert result.path == SuggestedPath.PROFESSIONAL_HELP
        assert result.matched_rule_id == "ask_for_help_always_professional"

    def test_is_unconditional_regardless_of_feelings_or_time(self):
        """The whole point of this rule: it must never be shifted by
        anything else, unlike Rule 2's modifier."""
        result = route_checkin(
            [Feeling.LONELY, Feeling.EXHAUSTED], Need.ASK_FOR_HELP, TimeOfDay.NIGHT
        )
        assert result.path == SuggestedPath.PROFESSIONAL_HELP


class TestLonelyAtNightModifier:
    """The one rule where feelings+time genuinely change the path — needs
    the most scrutiny, including proving it does NOT over-fire."""

    @pytest.mark.parametrize("need", [Need.DISTRACTION, Need.RELAX, Need.GET_MOTIVATED])
    @pytest.mark.parametrize("time_of_day", [TimeOfDay.EVENING, TimeOfDay.NIGHT])
    def test_fires_for_eligible_needs_at_night_or_evening_when_lonely(self, need, time_of_day):
        result = route_checkin([Feeling.LONELY], need, time_of_day)
        assert result.path == SuggestedPath.PRESENCE_MODE
        assert result.matched_rule_id == "lonely_at_night_prefers_presence"

    @pytest.mark.parametrize("time_of_day", [TimeOfDay.MORNING, TimeOfDay.AFTERNOON])
    def test_does_not_fire_during_the_day_even_if_lonely(self, time_of_day):
        result = route_checkin([Feeling.LONELY], Need.RELAX, time_of_day)
        assert result.path == SuggestedPath.TINY_ACTION
        assert result.matched_rule_id != "lonely_at_night_prefers_presence"

    def test_does_not_fire_at_night_without_lonely_in_feelings(self):
        result = route_checkin([Feeling.EXHAUSTED], Need.RELAX, TimeOfDay.NIGHT)
        assert result.path == SuggestedPath.TINY_ACTION
        assert result.matched_rule_id != "lonely_at_night_prefers_presence"

    def test_does_not_fire_for_non_eligible_needs_even_when_lonely_at_night(self):
        """study/be_around_people/talk/ask_for_help/understand_feeling
        have their own explicit rules and should never be shifted by this
        modifier, even when lonely+night is true."""
        result = route_checkin([Feeling.LONELY], Need.STUDY, TimeOfDay.NIGHT)
        assert result.path == SuggestedPath.TINY_ACTION
        assert result.matched_rule_id == "study"

    def test_ask_for_help_overrides_even_this_modifier(self):
        """Rule ordering check: ask_for_help is evaluated FIRST, so even a
        lonely-at-night ask_for_help case must stay professional_help."""
        result = route_checkin([Feeling.LONELY], Need.ASK_FOR_HELP, TimeOfDay.NIGHT)
        assert result.path == SuggestedPath.PROFESSIONAL_HELP


class TestDirectNeedMappings:
    def test_study_routes_to_tiny_action(self):
        result = route_checkin([Feeling.ANXIOUS], Need.STUDY, TimeOfDay.AFTERNOON)
        assert result.path == SuggestedPath.TINY_ACTION
        assert result.matched_rule_id == "study"

    def test_be_around_people_routes_to_presence_mode(self):
        result = route_checkin([Feeling.LONELY], Need.BE_AROUND_PEOPLE, TimeOfDay.AFTERNOON)
        assert result.path == SuggestedPath.PRESENCE_MODE
        assert result.matched_rule_id == "be_around_people"

    def test_talk_routes_to_presence_mode(self):
        result = route_checkin([Feeling.SAD], Need.TALK, TimeOfDay.MORNING)
        assert result.path == SuggestedPath.PRESENCE_MODE
        assert result.matched_rule_id == "talk"

    def test_get_motivated_routes_to_tiny_action(self):
        result = route_checkin([Feeling.UNMOTIVATED], Need.GET_MOTIVATED, TimeOfDay.MORNING)
        assert result.path == SuggestedPath.TINY_ACTION
        assert result.matched_rule_id == "get_motivated"

    def test_relax_routes_to_tiny_action(self):
        result = route_checkin([Feeling.EXHAUSTED], Need.RELAX, TimeOfDay.AFTERNOON)
        assert result.path == SuggestedPath.TINY_ACTION
        assert result.matched_rule_id == "relax"

    def test_distraction_routes_to_tiny_action(self):
        result = route_checkin([Feeling.ANXIOUS], Need.DISTRACTION, TimeOfDay.AFTERNOON)
        assert result.path == SuggestedPath.TINY_ACTION
        assert result.matched_rule_id == "distraction"


class TestUnderstandFeeling:
    def test_with_dont_know_uses_the_unclear_variant(self):
        result = route_checkin(
            [Feeling.DONT_KNOW], Need.UNDERSTAND_FEELING, TimeOfDay.AFTERNOON
        )
        assert result.path == SuggestedPath.TINY_ACTION
        assert result.matched_rule_id == "understand_feeling_unclear"

    def test_with_a_named_feeling_uses_the_named_variant(self):
        result = route_checkin([Feeling.SAD], Need.UNDERSTAND_FEELING, TimeOfDay.AFTERNOON)
        assert result.path == SuggestedPath.TINY_ACTION
        assert result.matched_rule_id == "understand_feeling_named"
        assert "sad" in result.reason

    def test_dont_know_combined_with_a_named_feeling_still_uses_unclear_variant(self):
        """dont_know present at all (even alongside a named feeling) should
        use the "unclear" framing, since the ordered rules check dont_know
        first — this pins down that intentional priority."""
        result = route_checkin(
            [Feeling.SAD, Feeling.DONT_KNOW], Need.UNDERSTAND_FEELING, TimeOfDay.AFTERNOON
        )
        assert result.matched_rule_id == "understand_feeling_unclear"


class TestReasonTextPersonalization:
    def test_single_feeling_phrasing(self):
        result = route_checkin([Feeling.LONELY], Need.STUDY, TimeOfDay.AFTERNOON)
        assert "feeling lonely" in result.reason

    def test_two_feelings_uses_and(self):
        result = route_checkin(
            [Feeling.LONELY, Feeling.EXHAUSTED], Need.STUDY, TimeOfDay.AFTERNOON
        )
        assert "lonely and exhausted" in result.reason

    def test_three_plus_feelings_uses_oxford_comma(self):
        result = route_checkin(
            [Feeling.LONELY, Feeling.EXHAUSTED, Feeling.ANXIOUS],
            Need.STUDY,
            TimeOfDay.AFTERNOON,
        )
        assert "lonely, exhausted, and anxious" in result.reason

    def test_dont_know_has_natural_phrasing_not_the_raw_tag(self):
        result = route_checkin([Feeling.DONT_KNOW], Need.STUDY, TimeOfDay.AFTERNOON)
        assert "dont_know" not in result.reason
        assert "not sure what to call it" in result.reason

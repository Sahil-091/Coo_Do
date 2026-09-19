"""
Deterministic Check-In routing rules — R&D doc Section 5.2 / Section 20.

This is the entire recommendation engine for Phase 3. No LLM, no ML
model, no hidden logic — a plain ordered list of rules, evaluated top
to bottom, first match wins. Read it top to bottom and you know exactly
what the system does; that legibility is the point (Section 20:
"we need to be able to audit and edit it directly").

Design principle: the student's STATED NEED is authoritative — we never
override what they explicitly asked for. FEELINGS and TIME_OF_DAY only
do two things: (a) personalize the reason text, and (b) in exactly ONE
well-motivated case (Rule 2 below), shift which of two reasonable paths
fits best, when the need alone doesn't clearly decide it. Anything
beyond that risks being paternalistic — see R&D doc Persona 7
("overwhelmed, refuses professional help") for why overriding a
student's stated choice is something this system deliberately avoids.
"""

from __future__ import annotations

import enum
from collections.abc import Callable
from dataclasses import dataclass


class Feeling(enum.StrEnum):
    LONELY = "lonely"
    SAD = "sad"
    ANXIOUS = "anxious"
    OVERWHELMED = "overwhelmed"
    ANGRY = "angry"
    EMPTY = "empty"
    EXHAUSTED = "exhausted"
    UNMOTIVATED = "unmotivated"
    CONFUSED = "confused"
    DONT_KNOW = "dont_know"


class Need(enum.StrEnum):
    TALK = "talk"
    DISTRACTION = "distraction"
    UNDERSTAND_FEELING = "understand_feeling"
    GET_MOTIVATED = "get_motivated"
    BE_AROUND_PEOPLE = "be_around_people"
    STUDY = "study"
    RELAX = "relax"
    ASK_FOR_HELP = "ask_for_help"


class TimeOfDay(enum.StrEnum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class SuggestedPath(enum.StrEnum):
    TINY_ACTION = "tiny_action"
    PRESENCE_MODE = "presence_mode"
    PROFESSIONAL_HELP = "professional_help"


_FEELING_PHRASES: dict[Feeling, str] = {
    Feeling.LONELY: "lonely",
    Feeling.SAD: "sad",
    Feeling.ANXIOUS: "anxious",
    Feeling.OVERWHELMED: "overwhelmed",
    Feeling.ANGRY: "angry",
    Feeling.EMPTY: "empty",
    Feeling.EXHAUSTED: "exhausted",
    Feeling.UNMOTIVATED: "unmotivated",
    Feeling.CONFUSED: "confused",
    Feeling.DONT_KNOW: "not sure what to call it",
}


def _describe_feelings(feelings: list[Feeling]) -> str:
    """Natural-language, Oxford-comma join: 'lonely', 'lonely and tired',
    'lonely, tired, and anxious'."""
    phrases = [_FEELING_PHRASES[f] for f in feelings]
    if len(phrases) == 1:
        return phrases[0]
    if len(phrases) == 2:
        return f"{phrases[0]} and {phrases[1]}"
    return ", ".join(phrases[:-1]) + f", and {phrases[-1]}"


@dataclass(frozen=True)
class CheckInInput:
    feelings: list[Feeling]
    need: Need
    time_of_day: TimeOfDay


@dataclass(frozen=True)
class RoutingResult:
    path: SuggestedPath
    reason: str
    matched_rule_id: str  # kept in the response for auditability/debugging


@dataclass(frozen=True)
class RoutingRule:
    id: str
    description: str  # human-readable, shown nowhere to students — this
    # is the audit trail: read `description` top to bottom and you have
    # the entire routing logic in plain English.
    matches: Callable[[CheckInInput], bool]
    build_reason: Callable[[CheckInInput], str]
    path: SuggestedPath


def _night_word(time_of_day: TimeOfDay) -> str:
    return "Nights" if time_of_day == TimeOfDay.NIGHT else "Evenings"


RULES: list[RoutingRule] = [
    RoutingRule(
        id="ask_for_help_always_professional",
        description=(
            "If the student explicitly asked for help, always route to "
            "professional help — unconditionally, no feeling/time check. "
            "Honoring a direct request outranks everything else."
        ),
        matches=lambda i: i.need == Need.ASK_FOR_HELP,
        build_reason=lambda i: (
            "You said you want to ask for help — that's a real step on its "
            "own. Here's a low-pressure way to actually do it."
        ),
        path=SuggestedPath.PROFESSIONAL_HELP,
    ),
    RoutingRule(
        id="lonely_at_night_prefers_presence",
        description=(
            "If the need is distraction/relax/get_motivated (which would "
            "otherwise default to a solo tiny action) AND the student "
            "feels lonely AND it's evening or night, suggest presence "
            "mode instead — this is the one place feelings+time genuinely "
            "shift the path, grounded in the R&D doc's own 'lonely at "
            "night' pattern (Persona 4). Not a general override rule."
        ),
        matches=lambda i: (
            i.need in (Need.DISTRACTION, Need.RELAX, Need.GET_MOTIVATED)
            and Feeling.LONELY in i.feelings
            and i.time_of_day in (TimeOfDay.EVENING, TimeOfDay.NIGHT)
        ),
        build_reason=lambda i: (
            f"{_night_word(i.time_of_day)} can be hard to get through alone, "
            f"especially feeling {_describe_feelings(i.feelings)}. Being "
            "near other people right now — even without talking — might "
            "help more than doing this by yourself."
        ),
        path=SuggestedPath.PRESENCE_MODE,
    ),
    RoutingRule(
        id="study",
        description="Studying need -> a small, doable study-related step.",
        matches=lambda i: i.need == Need.STUDY,
        build_reason=lambda i: (
            f"Studying alone while feeling {_describe_feelings(i.feelings)} "
            "is rough. One small, doable step might make it feel less stuck."
        ),
        path=SuggestedPath.TINY_ACTION,
    ),
    RoutingRule(
        id="be_around_people",
        description="Direct request to be around people -> presence mode.",
        matches=lambda i: i.need == Need.BE_AROUND_PEOPLE,
        build_reason=lambda _i: (
            "Wanting to be around people is exactly what this is for. "
            "No talking required if you don't want to."
        ),
        path=SuggestedPath.PRESENCE_MODE,
    ),
    RoutingRule(
        id="talk",
        description="Wanting to talk -> presence mode (conversation starts with proximity).",
        matches=lambda i: i.need == Need.TALK,
        build_reason=lambda _i: (
            "Wanting to talk to someone starts with being somewhere "
            "people actually are."
        ),
        path=SuggestedPath.PRESENCE_MODE,
    ),
    RoutingRule(
        id="get_motivated",
        description="Low motivation -> one small step (behavioral activation).",
        matches=lambda i: i.need == Need.GET_MOTIVATED,
        build_reason=lambda _i: (
            "Motivation usually shows up after you start, not before. "
            "One small step is enough to begin."
        ),
        path=SuggestedPath.TINY_ACTION,
    ),
    RoutingRule(
        id="relax",
        description="Wanting to relax -> a low-effort tiny action.",
        matches=lambda i: i.need == Need.RELAX,
        build_reason=lambda _i: (
            "A small, low-effort step toward rest — nothing that needs "
            "energy you don't have right now."
        ),
        path=SuggestedPath.TINY_ACTION,
    ),
    RoutingRule(
        id="distraction",
        description="Wanting distraction -> a small task to redirect attention.",
        matches=lambda i: i.need == Need.DISTRACTION,
        build_reason=lambda _i: (
            "A small task can be a good way to redirect your mind for a bit."
        ),
        path=SuggestedPath.TINY_ACTION,
    ),
    RoutingRule(
        id="understand_feeling_unclear",
        description=(
            "Wants to understand their feeling AND selected dont_know -> "
            "a concrete action framed as often clarifying more than "
            "sitting with the question."
        ),
        matches=lambda i: (
            i.need == Need.UNDERSTAND_FEELING and Feeling.DONT_KNOW in i.feelings
        ),
        build_reason=lambda _i: (
            "Not knowing exactly what you're feeling is really common. A "
            "small, concrete action can sometimes make it clearer than "
            "sitting with the question."
        ),
        path=SuggestedPath.TINY_ACTION,
    ),
    RoutingRule(
        id="understand_feeling_named",
        description=(
            "Wants to understand a feeling they already named (not "
            "dont_know) -> a small action framed as helping it settle."
        ),
        matches=lambda i: i.need == Need.UNDERSTAND_FEELING,
        build_reason=lambda i: (
            f"You already have some sense that this is {_describe_feelings(i.feelings)} "
            "— a small step can help it settle rather than spiral."
        ),
        path=SuggestedPath.TINY_ACTION,
    ),
]

_DEFAULT_REASON = "Here's one small, doable thing that might help right now."


def route_checkin(
    feelings: list[Feeling], need: Need, time_of_day: TimeOfDay
) -> RoutingResult:
    """
    The entire recommendation engine. Evaluates RULES top to bottom,
    first match wins. Every Need value is covered by exactly one
    unconditional rule below its conditional variants (see RULES), so
    the fallback should be unreachable in practice — it exists only as
    a defensive default, never silently returning nothing.
    """
    check_in = CheckInInput(feelings=feelings, need=need, time_of_day=time_of_day)
    for rule in RULES:
        if rule.matches(check_in):
            return RoutingResult(
                path=rule.path,
                reason=rule.build_reason(check_in),
                matched_rule_id=rule.id,
            )
    return RoutingResult(
        path=SuggestedPath.TINY_ACTION,
        reason=_DEFAULT_REASON,
        matched_rule_id="fallback_default",
    )

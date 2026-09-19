"""Opt-in live Gemini evaluation for Phase 6's bounded Voice Layer.

Run only with an intentionally supplied GEMINI_API_KEY; this script never
runs as part of the unit suite. It prints a small, reviewable batch of real
provider outputs and whether the deterministic eight-rule guard accepted each
one. The inputs are the fixed Phase 3 tag vocabulary and curated action copy,
not student text.

PowerShell:
  $env:PYTHONPATH='backend;backend/services/core-api'
  $env:GEMINI_API_KEY='...'
  python scripts/run_live_tiny_action_voice_evaluation.py
"""
from __future__ import annotations

import json
import os
import sys

from app.tiny_action_voice import TinyActionVoiceInput, generate_tiny_action_message


CASES = (
    TinyActionVoiceInput(
        feelings=("lonely",),
        stated_need="talk",
        action_title="Sit in the library for five minutes",
        difficulty_level=2,
        time_of_day="night",
    ),
    TinyActionVoiceInput(
        feelings=("anxious", "overwhelmed"),
        stated_need="study",
        action_title="Open one lecture slide",
        difficulty_level=1,
        time_of_day="morning",
    ),
    TinyActionVoiceInput(
        feelings=("empty", "exhausted"),
        stated_need="relax",
        action_title="Put your phone down for two minutes",
        difficulty_level=1,
        time_of_day="night",
    ),
    TinyActionVoiceInput(
        feelings=("dont_know",),
        stated_need="be_around_people",
        action_title="Sit in a shared study space",
        difficulty_level=3,
        time_of_day="evening",
    ),
)


def main() -> int:
    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY is required for the opt-in live evaluation.", file=sys.stderr)
        return 2

    passed = True
    for voice_input in CASES:
        result = generate_tiny_action_message(voice_input)
        review = {
            "input": voice_input.as_provider_payload(),
            "output": result.message,
            "fallback_reason": result.fallback_reason,
            "audits": [audit.__dict__ for audit in result.audits],
            "accepted_by_eight_rule_guard": result.message is not None,
        }
        print(json.dumps(review, ensure_ascii=False))
        passed = passed and result.message is not None

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

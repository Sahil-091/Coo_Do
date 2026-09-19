"""Opt-in Gemini evaluation. Requires GEMINI_API_KEY; never runs in unit tests.

This is a regression signal, not validation of clinical quality. Any crisis or
elevated miss exits non-zero. Adjacent false positives are reported but do not
pass the evaluation by being silently ignored.
"""
import json
from pathlib import Path

from app.gemini_classifier import ClassifierUnavailable, classify_text

ORDER = {"none": 0, "elevated": 1, "crisis": 2}
TEST_SET = Path(__file__).parent.parent / "tests" / "crisis_language_test_set.json"


def main() -> None:
    cases = json.loads(TEST_SET.read_text(encoding="utf-8"))
    failures: list[str] = []
    false_positives: list[str] = []
    for case in cases:
        actual = classify_text(case["text"])
        expected = case["expected_minimum"]
        print(f"{case['id']}: expected minimum={expected}, actual={actual}")
        if ORDER[actual] < ORDER[expected]:
            failures.append(case["id"])
        if expected == "none" and actual != "none":
            false_positives.append(case["id"])
    print(f"Misses: {failures or 'none'}")
    print(f"Adjacent false positives (review expected): {false_positives or 'none'}")
    if failures:
        raise SystemExit("Unsafe evaluation result: crisis/elevated cases were missed")


if __name__ == "__main__":
    try:
        main()
    except ClassifierUnavailable as error:
        raise SystemExit(f"Evaluation could not run: {error}") from error

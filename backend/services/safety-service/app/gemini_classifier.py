"""Narrow Gemini crisis-language classifier. It returns a flag only, never support prose.

This is an intentionally constrained mitigation, not a dedicated, purpose-trained
safety classifier. General-purpose LLM classification can miss crisis language and
must be reviewed/replaced if a dedicated validated provider becomes available.
"""
import json
import urllib.error
import urllib.request

from app.config import settings

PROMPT_VERSION = "crisis-classifier-v1"
VALID_FLAG_LEVELS = frozenset({"none", "elevated", "crisis"})

SYSTEM_PROMPT = """You are a narrow crisis-language classifier for a student wellbeing product.
Return only the requested JSON object. Do not give advice, explanations, diagnoses, or reassurance.
Classify the supplied text into exactly one flag_level:
- crisis: possible imminent self-harm, suicide, harm to others, or immediate danger.
- elevated: serious distress, hopelessness, self-harm references without clear imminent intent, or language that warrants showing crisis resources.
- none: no crisis-indicative language.
When uncertain, choose the more protective higher level. Metaphorical academic frustration alone is not crisis."""


class ClassifierUnavailable(RuntimeError):
    """The caller must fail safe and show deterministic resources when this is raised."""


def classify_text(text: str) -> str:
    if not settings.gemini_api_key:
        raise ClassifierUnavailable("GEMINI_API_KEY is not configured")

    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 24,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "object",
                "properties": {
                    "flag_level": {"type": "string", "enum": ["none", "elevated", "crisis"]}
                },
                "required": ["flag_level"],
            },
        },
    }
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": settings.gemini_api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 - fixed Google URL
            body = json.loads(response.read().decode())
        raw_text = body["candidates"][0]["content"]["parts"][0]["text"]
        return parse_flag_level(raw_text)
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
        raise ClassifierUnavailable("Gemini classification failed") from exc


def parse_flag_level(raw_text: str) -> str:
    """Treat malformed or unexpected provider output as unavailable, never as safe."""
    try:
        value = json.loads(raw_text)["flag_level"]
    except (TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ClassifierUnavailable("Gemini returned an invalid structured response") from exc
    if value not in VALID_FLAG_LEVELS:
        raise ClassifierUnavailable("Gemini returned an unsupported flag level")
    return value

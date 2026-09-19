"""Tiny Action Voice Layer — one bounded model call, never a conversation.

The public entry point in this module is ``generate_tiny_action_message``.
It deliberately accepts only the fixed tags produced by the check-in and a
curated Tiny Action.  It must never be repurposed to accept browser text,
retain conversational state, or compose crisis support.  See R&D doc Section
10 and Build_Prompt_Sequence.md, Phase 6.

Gemini is the current prototype provider.  ``TinyActionVoiceProvider`` keeps
the provider seam small so a self-hosted implementation can replace just the
adapter, without changing routes or the UI contract.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Literal, Protocol

from app.config import settings

PROMPT_VERSION = "tiny-action-voice-v1"
MAX_MESSAGE_CHARACTERS = 420
MAX_SENTENCES = 3
MAX_PROVIDER_ATTEMPTS = 2

# These are a defense-in-depth stop, not a replacement for Phase 5.  Phase 3
# supplies enums and curated content only, so there should be no route for
# crisis language to reach this module.  If that invariant is ever broken,
# do not send the value on to a generative model.
_CRISIS_ADJACENT_PATTERNS = (
    "suicide",
    "suicidal",
    "self-harm",
    "self harm",
    "kill myself",
    "end my life",
    "hurt myself",
    "harm myself",
    "hurt someone",
    "harm someone",
    "immediate danger",
)

_NEED_PHRASES = {
    "talk": "someone to talk to",
    "distraction": "a little distraction",
    "understand_feeling": "understanding what you are feeling",
    "get_motivated": "getting started",
    "be_around_people": "being around people",
    "study": "studying",
    "relax": "a little rest",
    "ask_for_help": "asking for help",
}
_FEELING_PHRASES = {"dont_know": "not sure what to call it"}

SYSTEM_PROMPT = """You phrase one already-selected Tiny Action for a student wellbeing product.
This is not therapy, a crisis service, or a conversation. Return JSON only, matching the supplied schema.

Use only the structured fields supplied in the user JSON. Do not infer private facts or mention a diagnosis.
For status=message, write one to three short, plain, warm sentences. It must:
- include the exact action title, one supplied feeling phrase, and the supplied need phrase;
- make the action explicitly optional by using the exact words "If you're up for it";
- not ask a question, give a command, or invite a reply;
- not claim to fix, cure, solve, diagnose, guarantee, or provide therapy.
Do not add any action other than the supplied action title.

Hard stop: if any supplied field is crisis-adjacent (self-harm, suicide, harm to another person, or immediate danger), return status=refusal and an empty message. Never write crisis support or advice yourself; the deterministic Safety Center flow owns that copy."""


@dataclass(frozen=True)
class TinyActionVoiceInput:
    feelings: tuple[str, ...]
    stated_need: str
    action_title: str
    difficulty_level: int
    time_of_day: str

    def as_provider_payload(self) -> dict[str, object]:
        return {
            "feelings": [
                _FEELING_PHRASES.get(feeling, feeling.replace("_", " "))
                for feeling in self.feelings
            ],
            "need_phrase": _NEED_PHRASES.get(self.stated_need, self.stated_need.replace("_", " ")),
            "action_title": self.action_title,
            "difficulty_level": self.difficulty_level,
            "time_of_day": self.time_of_day,
        }


@dataclass(frozen=True)
class VoiceCallAudit:
    """Metadata only — neither user inputs nor generated prose are retained."""

    provider: str
    model: str
    prompt_version: str
    attempt_number: int
    outcome: Literal["accepted", "rejected", "unavailable", "refused"]


@dataclass(frozen=True)
class TinyActionVoiceGeneration:
    message: str | None
    fallback_reason: Literal["unavailable", "rule_rejected", "refused", "crisis_input"] | None
    audits: tuple[VoiceCallAudit, ...]


class TinyActionVoiceProvider(Protocol):
    """The only provider-specific boundary Phase 6 needs to preserve."""

    provider_name: str
    model_name: str
    prompt_version: str

    def generate_tiny_action_message(self, voice_input: TinyActionVoiceInput) -> str | None:
        """Return a message, None for the model's hard-stop refusal, or raise if unavailable."""


class VoiceProviderUnavailable(RuntimeError):
    """Provider/network/format failure; the route must use Phase 4's static copy."""


class GeminiTinyActionVoiceProvider:
    """Current adapter only; replace this class to use self-hosted weights later."""

    provider_name = "gemini"
    prompt_version = PROMPT_VERSION

    def __init__(self) -> None:
        self.model_name = settings.gemini_model

    def generate_tiny_action_message(self, voice_input: TinyActionVoiceInput) -> str | None:
        if not settings.gemini_api_key:
            raise VoiceProviderUnavailable("GEMINI_API_KEY is not configured")

        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": json.dumps(voice_input.as_provider_payload())}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 180,
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["message", "refusal"]},
                        "message": {"type": "string"},
                    },
                    "required": ["status", "message"],
                },
            },
        }
        request = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "x-goog-api-key": settings.gemini_api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=settings.tiny_action_voice_timeout_seconds) as response:  # noqa: S310 - fixed Google URL
                body = json.loads(response.read().decode())
            raw_text = body["candidates"][0]["content"]["parts"][0]["text"]
            return _parse_provider_response(raw_text)
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            KeyError,
            IndexError,
            TypeError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise VoiceProviderUnavailable("Gemini Tiny Action Voice call failed") from exc


def _parse_provider_response(raw_text: str) -> str | None:
    """Parse only the schema we asked Gemini for; malformed output is never surfaced."""
    try:
        value = json.loads(raw_text)
        status = value["status"]
        message = value["message"]
    except (TypeError, KeyError, json.JSONDecodeError) as exc:
        raise VoiceProviderUnavailable("Gemini returned invalid structured voice output") from exc
    if status == "refusal":
        return None
    if status != "message" or not isinstance(message, str):
        raise VoiceProviderUnavailable("Gemini returned an unsupported voice output")
    return message


def _contains_crisis_adjacent_content(voice_input: TinyActionVoiceInput) -> bool:
    haystack = " ".join(
        (*voice_input.feelings, voice_input.stated_need, voice_input.action_title, voice_input.time_of_day)
    ).casefold()
    return any(pattern in haystack for pattern in _CRISIS_ADJACENT_PATTERNS)


def _sentence_count(message: str) -> int:
    # A final punctuation mark is optional; this still counts a short final
    # sentence and intentionally treats punctuation runs as one boundary.
    return len([part for part in re.split(r"[.!]+(?:\s+|$)", message.strip()) if part.strip()])


def is_rule_adherent(message: str, voice_input: TinyActionVoiceInput) -> bool:
    """Deterministic post-condition before any model prose reaches a student."""
    normalized = " ".join(message.split())
    lower = normalized.casefold()
    payload = voice_input.as_provider_payload()
    feeling_phrases = tuple(str(value).casefold() for value in payload["feelings"])
    need_phrase = str(payload["need_phrase"]).casefold()

    return (
        bool(normalized)
        and len(normalized) <= MAX_MESSAGE_CHARACTERS
        and 1 <= _sentence_count(normalized) <= MAX_SENTENCES
        and "?" not in normalized
        and "if you're up for it" in lower
        and voice_input.action_title.casefold() in lower
        and any(feeling in lower for feeling in feeling_phrases)
        and need_phrase in lower
        and not any(word in lower for word in ("fix", "cure", "solve", "diagnos", "guarantee", "therapy"))
    )


def generate_tiny_action_message(
    voice_input: TinyActionVoiceInput, provider: TinyActionVoiceProvider | None = None
) -> TinyActionVoiceGeneration:
    """Generate once, repair once, then return metadata for a static fallback.

    The caller owns the pre-written fallback content because it already has the
    Phase 4 action description.  This function never manufactures fallback
    prose, which keeps the failure path deterministic as well.
    """
    resolved_provider = provider or GeminiTinyActionVoiceProvider()
    if _contains_crisis_adjacent_content(voice_input):
        return TinyActionVoiceGeneration(
            message=None,
            fallback_reason="crisis_input",
            audits=(),
        )

    audits: list[VoiceCallAudit] = []
    for attempt_number in range(1, MAX_PROVIDER_ATTEMPTS + 1):
        try:
            message = resolved_provider.generate_tiny_action_message(voice_input)
        except VoiceProviderUnavailable:
            audits.append(
                VoiceCallAudit(
                    provider=resolved_provider.provider_name,
                    model=resolved_provider.model_name,
                    prompt_version=resolved_provider.prompt_version,
                    attempt_number=attempt_number,
                    outcome="unavailable",
                )
            )
            return TinyActionVoiceGeneration(
                message=None,
                fallback_reason="unavailable",
                audits=tuple(audits),
            )

        if message is None:
            audits.append(
                VoiceCallAudit(
                    provider=resolved_provider.provider_name,
                    model=resolved_provider.model_name,
                    prompt_version=resolved_provider.prompt_version,
                    attempt_number=attempt_number,
                    outcome="refused",
                )
            )
            return TinyActionVoiceGeneration(
                message=None,
                fallback_reason="refused",
                audits=tuple(audits),
            )

        if is_rule_adherent(message, voice_input):
            audits.append(
                VoiceCallAudit(
                    provider=resolved_provider.provider_name,
                    model=resolved_provider.model_name,
                    prompt_version=resolved_provider.prompt_version,
                    attempt_number=attempt_number,
                    outcome="accepted",
                )
            )
            return TinyActionVoiceGeneration(
                message=" ".join(message.split()),
                fallback_reason=None,
                audits=tuple(audits),
            )

        audits.append(
            VoiceCallAudit(
                provider=resolved_provider.provider_name,
                model=resolved_provider.model_name,
                prompt_version=resolved_provider.prompt_version,
                attempt_number=attempt_number,
                outcome="rejected",
            )
        )

    return TinyActionVoiceGeneration(
        message=None,
        fallback_reason="rule_rejected",
        audits=tuple(audits),
    )

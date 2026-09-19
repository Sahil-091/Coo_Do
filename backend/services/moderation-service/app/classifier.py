"""Conservative deterministic pre-publication classifiers for Phase 12."""
import re

TOXICITY_PATTERNS = (r"\b(kill yourself|go die|you should die)\b", r"\b(stupid (?:idiot|bitch)|worthless (?:idiot|loser))\b")
SEXUAL_PATTERNS = (r"\b(nudes?|send pics|hook ?up|explicit sexual)\b",)
SCAM_PATTERNS = (r"\b(crypto giveaway|guaranteed returns|send money|wire transfer)\b", r"https?://\S+.*https?://\S+")
CONTACT_OR_LOCATION_PATTERNS = (
    r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b",
    r"\b(?:\+?\d[\s-]?){8,}\d\b",
    r"\b(?:meet me|come over|my (?:hostel|flat|house|room) is)\b",
    # An address belongs in the verified venue catalogue, never title/body
    # text. Hold address-like copy rather than risk publishing a residence.
    r"\b\d{1,5}\s+(?:[a-z0-9.'-]+\s+){0,3}(?:street|st|road|rd|avenue|ave|lane|ln|flat|apartment|apt|house|hostel|room)\b",
)
OFF_PLATFORM_OR_DATING_PATTERNS = (
    r"\b(?:dm me|message me privately|move to (?:whatsapp|telegram|instagram)|add me on)\b",
    r"\b(?:date me|looking for (?:a )?(?:date|girlfriend|boyfriend)|hook ?up)\b",
)
_COMPILED = {
    "toxicity_or_harassment": tuple(re.compile(pattern, re.IGNORECASE) for pattern in TOXICITY_PATTERNS),
    "sexual_content": tuple(re.compile(pattern, re.IGNORECASE) for pattern in SEXUAL_PATTERNS),
    "spam_or_scam": tuple(re.compile(pattern, re.IGNORECASE) for pattern in SCAM_PATTERNS),
    # These rules are shown before posting. They are held conservatively for
    # a human reviewer rather than silently published or automatically removed.
    "personal_contact_or_location": tuple(re.compile(pattern, re.IGNORECASE) for pattern in CONTACT_OR_LOCATION_PATTERNS),
    "off_platform_or_dating_approach": tuple(re.compile(pattern, re.IGNORECASE) for pattern in OFF_PLATFORM_OR_DATING_PATTERNS),
}


def classify_non_safety(text: str) -> list[str]:
    """Return every conservative reason; any reason holds the post for review."""
    return [
        reason
        for reason, patterns in _COMPILED.items()
        if any(pattern.search(text) for pattern in patterns)
    ]

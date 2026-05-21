"""Detectors for voice-triggered system commands (e.g. language switching).

Each detector is a pure function: takes a transcript string, returns a value
or None. No backend state is touched here — keeps the regex layer easy to
unit-test in isolation.
"""

import re
from typing import Optional

_SWITCH_TO_SV_PATTERNS = (
    r"\bswitch\s+to\s+swedish\b",
    r"\bchange\s+to\s+swedish\b",
    r"\bspeak\s+swedish\b",
    r"\bin\s+swedish\b",
    r"\bswitch\s+to\s+sweden\b",
    r"\bchange\s+to\s+sweden\b",
    r"\bbyt\s+till\s+svenska\b",
    r"\bbyta\s+till\s+svenska\b",
    r"\bväxla\s+till\s+svenska\b",
    r"\bprata\s+svenska\b",
    r"\btala\s+svenska\b",
    r"\bbyt\s+till\s+sverige\b",
    r"\bväxla\s+till\s+sverige\b",
)

_SWITCH_TO_EN_PATTERNS = (
    r"\bswitch\s+to\s+english\b",
    r"\bchange\s+to\s+english\b",
    r"\bspeak\s+english\b",
    r"\bin\s+english\b",
    r"\bswitch\s+to\s+england\b",
    r"\bchange\s+to\s+england\b",
    r"\bbyt\s+till\s+engelska\b",
    r"\bbyta\s+till\s+engelska\b",
    r"\bväxla\s+till\s+engelska\b",
    r"\bprata\s+engelska\b",
    r"\btala\s+engelska\b",
    r"\bbyt\s+till\s+england\b",
    r"\bväxla\s+till\s+england\b",
)

_SV_REGEX = re.compile("|".join(_SWITCH_TO_SV_PATTERNS), re.IGNORECASE)
_EN_REGEX = re.compile("|".join(_SWITCH_TO_EN_PATTERNS), re.IGNORECASE)


def detect_language_switch_command(text: str) -> Optional[str]:
    """Return 'sv' or 'en' if the transcript asks to switch language, else None.

    Recognises common imperative phrasings in both English and Swedish.
    If both directions match (e.g. "switch from English to Swedish"), the
    earlier match in the string wins.
    """
    if not text:
        return None
    sv_match = _SV_REGEX.search(text)
    en_match = _EN_REGEX.search(text)
    if sv_match and not en_match:
        return "sv"
    if en_match and not sv_match:
        return "en"
    if sv_match and en_match:
        return "sv" if sv_match.start() < en_match.start() else "en"
    return None

"""Public TTS API.

Thin facade over the pluggable engine layer in `services.tts_engines`. Call
sites use `generate_tts_audio(text, language)` and stay engine-agnostic.
"""

from config import PIPER_MODELS
from services.tts_engines import PiperTTS

_piper = PiperTTS(PIPER_MODELS)


def generate_tts_audio(text: str, language: str | None = None) -> bytes:
    """Synthesize speech from text and return WAV bytes.

    `language` selects the voice ("en" or "sv"). If omitted, the current
    global language state is used. Returns empty bytes for word-less input.
    """
    if language is None:
        from state import language_state  # local import avoids circular dep
        language = language_state.get()
    return _piper.synthesize(text, language)

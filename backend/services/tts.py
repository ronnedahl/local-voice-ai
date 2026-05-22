"""Public TTS API + language-based engine routing.

Rest of the app calls `generate_tts_audio(text, language)` and stays
engine-agnostic. Routing rule: English → Kokoro (more natural), Swedish →
Piper (Kokoro doesn't support sv). Any failure on a non-Piper engine falls
back to Piper rather than 500ing — the Swedish demo path is sacred.
"""

import logging

from config import (
    KOKORO_DEFAULT_VOICE,
    KOKORO_MODEL,
    KOKORO_VOICES,
    PIPER_MODELS,
)
from services.tts_engines import KokoroTTS, PiperTTS, TTSEngine

logger = logging.getLogger(__name__)

_piper = PiperTTS(PIPER_MODELS)
_kokoro = KokoroTTS(KOKORO_MODEL, KOKORO_VOICES, KOKORO_DEFAULT_VOICE)

_ENGINE_BY_LANGUAGE: dict[str, TTSEngine] = {
    "en": _kokoro,
    "sv": _piper,
}


def generate_tts_audio(text: str, language: str | None = None) -> bytes:
    """Synthesize WAV bytes using the engine preferred for `language`.

    `language` selects the voice; if omitted, the global language state is
    used. Unknown languages fall back to Piper. If the preferred engine
    raises, we log and retry on Piper.
    """
    if language is None:
        from state import language_state  # local import avoids circular dep
        language = language_state.get()

    engine = _ENGINE_BY_LANGUAGE.get(language, _piper)

    try:
        return engine.synthesize(text, language)
    except Exception as e:
        if engine is _piper:
            raise
        logger.warning(
            "TTS engine failed for %r (%s); falling back to Piper: %s",
            language, type(engine).__name__, e,
        )
        return _piper.synthesize(text, language)

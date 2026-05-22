"""Pluggable TTS engines.

Each engine wraps a specific synthesis backend (Piper, Kokoro, ...) behind a
common interface so the rest of the app can stay engine-agnostic. Engines own
their own model loading, language→voice mapping, and audio format.
"""

from __future__ import annotations

import io
import re
import subprocess
import tempfile
import wave
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


def clean_text_for_tts(text: str) -> str:
    """Strip markdown so TTS doesn't read '**' as 'asterisk asterisk'."""
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"_+", "", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-+*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class TTSEngine(ABC):
    """Abstract TTS adapter.

    Implementations must return mono PCM WAV bytes. The router relies only on
    `synthesize()` and `supported_languages` — the rest is helper surface.
    """

    @property
    @abstractmethod
    def supported_languages(self) -> tuple[str, ...]:
        """Language codes this engine can synthesize, e.g. ('sv', 'en')."""

    @abstractmethod
    def synthesize(self, text: str, language: str, voice: str | None = None) -> bytes:
        """Render `text` to WAV bytes in the given language."""

    def list_voices(self, language: str) -> list[str]:
        """Default: no per-voice picker exposed."""
        return []


class PiperTTS(TTSEngine):
    """Piper CLI adapter. One ONNX voice model per supported language."""

    def __init__(self, models: dict[str, str]):
        self._models = models

    @property
    def supported_languages(self) -> tuple[str, ...]:
        return tuple(self._models.keys())

    def synthesize(self, text: str, language: str, voice: str | None = None) -> bytes:
        cleaned = clean_text_for_tts(text)
        if not re.search(r"\w", cleaned):
            return b""

        if language not in self._models:
            raise ValueError(f"No Piper voice configured for language {language!r}")
        model_path = self._models[language]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name

        try:
            result = subprocess.run(
                ["piper", "--model", model_path, "--output_file", output_path],
                input=cleaned,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Piper TTS failed: {result.stderr}")
            with open(output_path, "rb") as f:
                return f.read()
        finally:
            Path(output_path).unlink(missing_ok=True)


def _float32_to_wav_bytes(samples: "np.ndarray", sample_rate: int) -> bytes:
    """Convert a float32 mono numpy array (range [-1, 1]) to 16-bit PCM WAV bytes."""
    import numpy as np

    int16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(int16.tobytes())
    return buf.getvalue()


class KokoroTTS(TTSEngine):
    """Kokoro adapter via `kokoro-onnx`.

    Higher-quality English than Piper. Model is lazy-loaded on first
    `synthesize()` call so backend startup stays fast when Kokoro is unused.
    Returns 24 kHz mono PCM WAV.
    """

    # Our short codes → Kokoro's BCP-47-ish language codes
    _LANG_MAP = {"en": "en-us"}

    def __init__(self, model_path: str, voices_path: str, default_voice: str = "af_heart"):
        self._model_path = model_path
        self._voices_path = voices_path
        self._default_voice = default_voice
        self._kokoro = None  # lazy

    @property
    def supported_languages(self) -> tuple[str, ...]:
        return tuple(self._LANG_MAP.keys())

    def _ensure_loaded(self) -> None:
        if self._kokoro is not None:
            return
        for path in (self._model_path, self._voices_path):
            if not Path(path).is_file():
                raise FileNotFoundError(
                    f"Kokoro model file missing: {path}. "
                    f"Run scripts/download_kokoro_models.sh to fetch model files."
                )
        from kokoro_onnx import Kokoro  # heavy import, defer until needed

        print(f"Loading Kokoro from {self._model_path}...")
        self._kokoro = Kokoro(self._model_path, self._voices_path)
        print("Kokoro model loaded")

    def synthesize(self, text: str, language: str, voice: str | None = None) -> bytes:
        cleaned = clean_text_for_tts(text)
        if not re.search(r"\w", cleaned):
            return b""
        if language not in self._LANG_MAP:
            raise ValueError(f"Kokoro doesn't support language {language!r}")

        self._ensure_loaded()
        samples, sample_rate = self._kokoro.create(
            cleaned,
            voice=voice or self._default_voice,
            speed=1.0,
            lang=self._LANG_MAP[language],
        )
        return _float32_to_wav_bytes(samples, sample_rate)

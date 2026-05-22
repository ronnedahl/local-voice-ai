"""Pluggable TTS engines.

Each engine wraps a specific synthesis backend (Piper, Kokoro, ...) behind a
common interface so the rest of the app can stay engine-agnostic. Engines own
their own model loading, language→voice mapping, and audio format.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path


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

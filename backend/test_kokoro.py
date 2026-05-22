from services.tts_engines import KokoroTTS
from config import KOKORO_MODEL, KOKORO_VOICES, KOKORO_DEFAULT_VOICE

k = KokoroTTS(KOKORO_MODEL, KOKORO_VOICES, KOKORO_DEFAULT_VOICE)
wav = k.synthesize("Hello, this is the new Kokoro voice for the assistant.", "en")
with open("/tmp/kokoro_test.wav", "wb") as f:
    f.write(wav)
print(f"Wrote {len(wav)} bytes")
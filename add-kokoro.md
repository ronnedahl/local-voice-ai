# TTS Refactor: Pluggable Engine (Piper + Kokoro)

## Kontext

Repo: `local-voice-ai` — lokal voice assistant med Whisper (STT) → Ollama (LLM) → Piper (TTS), körs 100% lokalt via FastAPI backend + frontend. Stödjer svenska och engelska.

Nuvarande state: Piper är hårdkodad som enda TTS-motor.

## Mål

Refaktorera TTS-lagret till en pluggable arkitektur med två motorer:

- **Piper** — behålls för svenska
- **Kokoro** — används för engelska (bättre röstkvalitet, mindre robotisk)

Språkbaserad routing väljer motor automatiskt.

## Varför hybrid, inte full migration till Kokoro

Kokoro stödjer engelska (US/UK), franska, hindi, spanska, japanska, kinesiska, italienska och portugisiska — **men inte svenska**. Eftersom det primära use caset (pitch till Karlstad kommun, Samtalsstöd för äldreomsorg) kräver svenska kan Piper inte tas bort.

Kokoros engelska är däremot markant naturligare än Pipers, och det är vad rekryterare som testar appen kommer att höra.

Hybrid-approachen demonstrerar engineering judgment: utvärdera verktyg på deras faktiska styrkor i stället för att byta ut allt så fort något nytt dyker upp.

## Arkitektur

**Abstract TTS-interface** i backend:

- `synthesize(text, lang, voice) -> bytes` — returnerar WAV/PCM-audio
- `list_voices(lang) -> list[str]`
- Property: `supported_languages`

**Adapters:**

- `PiperTTS` — wrappar nuvarande Piper-integration
- `KokoroTTS` — ny adapter, använd `kokoro-onnx` (lättare än PyTorch-versionen, fungerar med befintligt onnxruntime-mönster)

**Router:**

- Input: `lang` (`sv`, `en`, ...)
- Logik:
  - `sv` → Piper
  - `en` → Kokoro
  - okänt språk → fallback till Piper (default)
- Möjlighet att override via env/config för testning

**Audio output-konsistens:**

- Båda motorer ska producera samma sample rate (rekommendation: 24000 Hz)
- Båda WAV/PCM 16-bit mono
- Resample inuti adaptern om motorns native rate skiljer sig — routern ska aldrig behöva veta om det

## Tasks (i ordning)

1. Definiera `TTSEngine` abstract interface
2. Flytta nuvarande Piper-kod till `PiperTTS`-adapter (ren refactor, ingen funktionsändring)
3. Verifiera att allt fungerar via adaptern — Piper-only path ska vara identisk med pre-refactor
4. Lägg till `KokoroTTS`-adapter (kokoro-onnx + voice model)
5. Implementera router (`get_tts_engine(lang)`)
6. Wire in router i API-endpoint som idag anropar Piper direkt
7. Lägg till config för default-motor per språk (env vars eller yaml)
8. Uppdatera `docker-compose.yml` för Kokoro model files
9. Uppdatera README — kort sektion "Why hybrid TTS"
10. Smoketest: svensk prompt → Piper-output, engelsk prompt → Kokoro-output

## Constraints

- **Bryt inte befintlig svensk funktionalitet.** Piper-pathen måste fungera identiskt efter refactor — testa innan Kokoro adderas.
- **Model files:** Kokoros `kokoro-v1.0.onnx` (~325MB) och `voices-v1.0.bin` (~30MB) ska läggas i `.gitignore` och laddas ner via setup-script, samma mönster som befintliga Piper-modeller.
- **GPU/CPU:** Kokoro stödjer båda via onnxruntime. Behåll samma flexibilitet som Piper har idag.
- **Voice mapping:** Kokoros röster har egna namn (`af_bella`, `af_heart`, `am_adam`, etc.). Mappa antingen till samma "voice"-parameter som frontend skickar, eller exponera per-engine voice lists via `list_voices()`.
- **Språkkod-normalisering:** Var konsekvent (`sv` / `en`, inte `sv-SE` / `en-US`). Normalisera input i routern om det är osäkert vad frontend skickar.
- **Felhantering:** Om Kokoro-adaptern kraschar för engelsk input, fall tillbaka till Piper i stället för att returnera 500. Logga warning.

## Out of scope (gör INTE i denna refactor)

- Streaming TTS
- Nya språk utöver `sv` / `en`
- Ändringar i Whisper (STT) eller Ollama (LLM)
- Frontend-ändringar utöver eventuell voice picker per språk
- Voice cloning eller fine-tuning
- Byte av befintlig docker-compose-struktur

## Definition of Done

- Repo bygger och kör utan errors från fresh clone
- Svensk prompt routar till Piper, audio matchar pre-refactor
- Engelsk prompt routar till Kokoro, audio är hörbart mer naturlig än Piper-engelska
- README beskriver hybrid-arkitekturen och varför valet gjordes
- `docker-compose up` startar hela stacken utan manuell intervention (förutom model download via script)
- Kommitmeddelanden berättar storyn: `refactor: extract TTS interface`, `feat: add Kokoro adapter`, `feat: language-based TTS routing`
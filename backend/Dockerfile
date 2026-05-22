FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System dependencies. espeak-ng is required by Kokoro's phonemizer.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    python3-venv \
    python3-pip \
    gcc \
    build-essential \
    curl \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

# Download Piper TTS voice models (Swedish + English fallback)
RUN mkdir -p /app/voices && \
    curl -L -o /app/voices/sv_SE-nst-medium.onnx \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/sv/sv_SE/nst/medium/sv_SE-nst-medium.onnx" && \
    curl -L -o /app/voices/sv_SE-nst-medium.onnx.json \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/sv/sv_SE/nst/medium/sv_SE-nst-medium.onnx.json" && \
    curl -L -o /app/voices/en_US-amy-medium.onnx \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx" && \
    curl -L -o /app/voices/en_US-amy-medium.onnx.json \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

# Download Kokoro TTS model files (more natural English voice)
RUN mkdir -p /app/voices/kokoro && \
    curl -L -o /app/voices/kokoro/kokoro-v1.0.onnx \
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx" && \
    curl -L -o /app/voices/kokoro/voices-v1.0.bin \
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

# Copy application code
COPY . .

ENV PIPER_MODEL_EN=/app/voices/en_US-amy-medium.onnx
ENV PIPER_MODEL_SV=/app/voices/sv_SE-nst-medium.onnx
ENV KOKORO_MODEL=/app/voices/kokoro/kokoro-v1.0.onnx
ENV KOKORO_VOICES=/app/voices/kokoro/voices-v1.0.bin
ENV OLLAMA_BASE_URL=http://ollama:11434

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

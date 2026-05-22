#!/usr/bin/env bash
#
# Download Kokoro TTS model files for the English voice.
#
# Default target: ~/.local/share/kokoro/  (matches the default paths in
# backend/config.py — KOKORO_MODEL and KOKORO_VOICES).
#
# Override with:  KOKORO_DIR=/some/other/dir scripts/download_kokoro_models.sh

set -euo pipefail

KOKORO_DIR="${KOKORO_DIR:-$HOME/.local/share/kokoro}"
MODEL_URL="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

mkdir -p "$KOKORO_DIR"

download() {
    local url="$1"
    local dest="$2"
    if [[ -f "$dest" ]]; then
        echo "skip: $dest already exists"
        return
    fi
    echo "downloading $(basename "$dest") -> $dest"
    curl -L --fail --progress-bar -o "$dest" "$url"
}

download "$MODEL_URL" "$KOKORO_DIR/kokoro-v1.0.onnx"
download "$VOICES_URL" "$KOKORO_DIR/voices-v1.0.bin"

echo
echo "Done. Files saved to: $KOKORO_DIR"
echo
echo "If you placed them elsewhere, set these env vars:"
echo "  KOKORO_MODEL=$KOKORO_DIR/kokoro-v1.0.onnx"
echo "  KOKORO_VOICES=$KOKORO_DIR/voices-v1.0.bin"

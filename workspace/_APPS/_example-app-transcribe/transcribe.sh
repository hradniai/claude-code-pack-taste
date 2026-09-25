#!/usr/bin/env bash
# transcribe.sh - STUB
#
# Convert a local audio/video file into a markdown transcript.
#
# This is the entry point for the transcribe example app. The actual API
# call is NOT YET IMPLEMENTED - you need to fill in the model invocation
# below for your chosen provider.
#
# Recommended providers:
#   - Google Gemini (multimodal, supports audio input directly)
#   - OpenAI transcription API (gpt-transcribe; audio-only)
#   - Local whisper.cpp (no API cost, requires install)
#
# Configuration: API keys in this app's own .env next to this script
# (schema: ~/.claude/templates/app-env.example)
#
# Usage:
#   transcribe.sh <input-file> [--language LANG]

set -euo pipefail

# --- Source credentials from this app's own .env ---
ENV_FILE="$(dirname "$0")/.env"
[ -f "$ENV_FILE" ] && { set -a; . "$ENV_FILE"; set +a; }

# --- Parse arguments ---
INPUT="${1:?Usage: transcribe.sh <input-file> [--language LANG]}"
shift

LANGUAGE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --language) LANGUAGE="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# --- Validate input ---
if [ ! -f "$INPUT" ]; then
  echo "Error: file not found: $INPUT" >&2
  exit 1
fi

OUTPUT="${INPUT%.*}.transcript.md"
echo "Input:  $INPUT"
echo "Output: $OUTPUT"
echo ""

# ============================================================================
# TODO: Implement the actual API call below for your chosen provider.
#
# Hints:
#
# Gemini (recommended for audio):
#   1. Upload file via Files API:
#      curl -X POST "https://generativelanguage.googleapis.com/upload/v1beta/files?key=$GEMINI_API_KEY" \
#        -H "Content-Type: $(file -b --mime-type "$INPUT")" \
#        --data-binary "@$INPUT"
#   2. Use the returned file URI in a generateContent call with prompt:
#      "Transcribe this audio. Output as markdown with speaker labels if
#       distinguishable. Add timestamps every 30 seconds."
#
# OpenAI transcription API (gpt-transcribe; whisper-1 is legacy):
#   curl https://api.openai.com/v1/audio/transcriptions \
#     -H "Authorization: Bearer $OPENAI_API_KEY" \
#     -F file="@$INPUT" \
#     -F model="gpt-transcribe" | jq -r .text
#
# Local whisper.cpp:
#   ./build/bin/whisper-cli -m models/ggml-large-v3.bin -f "$INPUT" -otxt
# ============================================================================

echo "ERROR: This is a stub. Implement the API call in $0 to make it work." >&2
exit 1

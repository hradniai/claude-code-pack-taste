---
type: core
title: "Transcribe (stub)"
status: approved
summary: "Local audio/video → markdown transcript via LLM API."
created: 2026-05-13 12:08
updated: 2026-09-23 13:30
owner: Šimon Hradní
client: ~
path: workspace/_APPS/_example-app-transcribe/README.md
tags: [readme]
version: "1.0.0"
release: latest
---

# Transcribe (stub)

Local audio/video → markdown transcript via LLM API.

> **Status:** stub. The script is documented but the API call is not yet implemented. See AGENTS.md for context.

## Quickstart (after implementation)

```bash
./transcribe.sh path/to/audio.mp3
```

## What you need to do to make this work

1. Pick a provider (Gemini, OpenAI, or local whisper.cpp)
2. Put the API key in this app's own `.env` (e.g. `GEMINI_API_KEY=...`): `cp ~/.claude/templates/app-env.example .env.example`, then `cp .env.example .env` and fill in the value yourself (Claude never reads or edits `.env`)
3. Implement the API call in `transcribe.sh` - see comments in the file for hints
4. Test on a known sample in `examples/`

## Why no working version is shipped

- API formats change frequently across providers
- Local tooling has per-platform setup that this starter pack can't assume
- Implementation forces you to make a deliberate choice instead of inheriting whatever the package author preferred

## Alternatives if you don't want to build this yourself

- `whisper.cpp` - local, free, runs on CPU/GPU, requires per-platform install
- OpenAI transcription API (`gpt-transcribe`, `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`; `whisper-1` is legacy) - easy API, billed per minute, returns text only. Anthropic's API does not accept audio input.
- Google Gemini multimodal API - supports audio directly in chat, often cheapest for casual use

## Removing the stub

If you don't want this app, move it aside (the pack denies recursive deletes; remove the backup yourself later if you like). The path assumes the default workspace root `~/Documents/`; use your own if you chose another:
```bash
mv ~/Documents/_APPS/_example-app-transcribe ~/Documents/_APPS/_example-app-transcribe.bak-$(date +%Y%m%d)
```

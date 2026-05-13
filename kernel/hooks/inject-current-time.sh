#!/usr/bin/env bash
# inject-current-time.sh — UserPromptSubmit hook.
#
# Claude Code's harness auto-injects today's date (`# currentDate`) into
# context but does NOT inject the current time. Without time, Claude tends
# to guess, often wrongly — visible in incorrect timestamps in notes.md.
#
# This hook fills the gap by adding the current local time to context on
# every user prompt. Token cost: ~20 tokens per turn.

set -uo pipefail

CURRENT_TIME=$(date '+%Y-%m-%d %H:%M')

cat <<JSON
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Current local time: $CURRENT_TIME (use this when writing timestamps to notes.md or other dated files)"
  }
}
JSON

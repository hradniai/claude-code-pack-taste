#!/usr/bin/env bash
# notes-research.sh
# Hook for PostToolUse on Edit|Write events.
#
# When a notes.md file is edited and there's any non-blank content after the
# last marker emoji (✅, 🔄, ⏭️) — or no markers at all — dispatches an
# Anthropic API call in the background. The model evaluates each unmarked
# item and either:
#   - performs research and writes a markdown report (marks with ✅), or
#   - judges that it doesn't warrant research (marks with ⏭️)
#
# Configuration (read from ~/.claude/.env):
#   ANTHROPIC_API_KEY  — required. Without it, this hook is a silent no-op.
#   ANTHROPIC_MODEL    — optional, defaults to claude-haiku-4-5-20251001
#
# Output: {project}/research/{topic-slug}-research-{YYYY-MM-DD}.md
# notes.md is updated with markers (✅/⏭️) and links to research files.
#
# Note: API calls without web search produce limited "research" — only the
# model's training knowledge. To enable real web research, add the web_search
# server tool to the API request payload below (search Anthropic docs for the
# current tool name; e.g. web_search_20250305).
#
# To disable: comment out this hook in ~/.claude/settings.json
#             or remove ANTHROPIC_API_KEY from ~/.claude/.env.

set -euo pipefail

# --- Source credentials from user-level env file ---
[ -f "$HOME/.claude/.env" ] && { set -a; . "$HOME/.claude/.env"; set +a; }

ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-claude-haiku-4-5-20251001}"

# --- Parse hook input from stdin ---
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# --- Guard clauses ---
[ -z "$FILE_PATH" ] && exit 0
[ "$(basename "$FILE_PATH")" != "notes.md" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# --- Format-agnostic detection: any non-blank content after the last marker? ---
LAST_MARKER_LINE=$(grep -nE '✅|🔄|⏭️' "$FILE_PATH" | tail -1 | cut -d: -f1)
LAST_MARKER_LINE=${LAST_MARKER_LINE:-0}

TAIL_CONTENT=$(awk -v ml="$LAST_MARKER_LINE" 'NR > ml' "$FILE_PATH" \
  | grep -vE '^[[:space:]]*$')

[ -z "$TAIL_CONTENT" ] && exit 0

# --- API key required; silent no-op if missing ---
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  exit 0
fi

# --- Lock per file to debounce rapid edits (10 min cooldown) ---
LOCK_DIR="/tmp/cc-starter-notes-research"
mkdir -p "$LOCK_DIR"
LOCK_SLUG=$(echo "$FILE_PATH" | sed 's|/|_|g')
LOCK_FILE="$LOCK_DIR/${LOCK_SLUG}.lock"
MAX_LOCK_AGE=600

if [ -f "$LOCK_FILE" ]; then
  LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || stat -c %Y "$LOCK_FILE") ))
  [ "$LOCK_AGE" -lt "$MAX_LOCK_AGE" ] && exit 0
  rm -f "$LOCK_FILE"
fi
touch "$LOCK_FILE"

# --- Generate output filename for potential research file ---
PROJECT_DIR=$(dirname "$FILE_PATH")
RESEARCH_DIR="$PROJECT_DIR/research"
mkdir -p "$RESEARCH_DIR"

SLUG=$(echo "$TAIL_CONTENT" | head -1 \
       | tr -cd 'a-zA-Z0-9 ' | tr ' ' '-' | tr '[:upper:]' '[:lower:]' \
       | cut -c1-50 | sed 's/^-*//;s/-*$//')
SLUG=${SLUG:-note}
DATE=$(date +%Y-%m-%d)
OUTPUT_FILE="$RESEARCH_DIR/${SLUG}-research-${DATE}.md"

# --- Background API call; never block the user's edit ---
(
  PROMPT_JSON=$(printf '%s' "$TAIL_CONTENT" | jq -Rs .)
  SYSTEM_PROMPT='You are a research assistant. Read the unmarked note(s) below.

For each note, decide:
1. If it warrants substantive research (factual question, comparison, deep technical topic, market analysis, etc.) → produce a comprehensive markdown report.
2. If it is a personal todo, reminder, opinion, or unresearchable thought → respond with the literal single line: SKIP

Output rules:
- If research is warranted: respond with the full markdown report only. No preamble.
- If not: respond with the single word SKIP and nothing else.
- Lead the report with a brief verdict, then detailed findings. Be specific, anti-hype, and explicit about uncertainty. Acknowledge what you do not know rather than fabricate.'
  SYSTEM_JSON=$(printf '%s' "$SYSTEM_PROMPT" | jq -Rs .)

  REQUEST_BODY=$(jq -n \
    --arg model "$ANTHROPIC_MODEL" \
    --argjson system "$SYSTEM_JSON" \
    --argjson prompt "$PROMPT_JSON" \
    '{
      model: $model,
      max_tokens: 4096,
      system: $system,
      messages: [{role: "user", content: $prompt}]
    }')

  RESPONSE=$(curl -sS https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d "$REQUEST_BODY" 2>&1)

  TEXT=$(echo "$RESPONSE" | jq -r '.content[]? | select(.type == "text") | .text' 2>/dev/null || true)

  if [ -z "$TEXT" ]; then
    {
      echo ""
      echo "  🔄 research dispatch failed at $(date '+%H:%M') — see API response for details"
    } >> "$FILE_PATH"
    rm -f "$LOCK_FILE"
    exit 0
  fi

  # Trim whitespace, check if it's the SKIP signal
  TRIMMED=$(echo "$TEXT" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')

  if [ "$TRIMMED" = "SKIP" ]; then
    {
      echo ""
      echo "  ⏭️ no research needed (judged by $ANTHROPIC_MODEL at $(date '+%H:%M'))"
    } >> "$FILE_PATH"
  else
    {
      echo "# ${SLUG//-/ }"
      echo ""
      echo "**Date:** $DATE"
      echo "**Triggered by:** unmarked entry in \`$FILE_PATH\`"
      echo "**Model:** $ANTHROPIC_MODEL"
      echo ""
      echo "---"
      echo ""
      echo "## Source note"
      echo ""
      echo "$TAIL_CONTENT"
      echo ""
      echo "---"
      echo ""
      echo "## Research"
      echo ""
      echo "$TEXT"
    } > "$OUTPUT_FILE"

    {
      echo ""
      echo "  ✅ research done at $(date '+%H:%M') → \`$OUTPUT_FILE\`"
    } >> "$FILE_PATH"
  fi

  rm -f "$LOCK_FILE"
) > /dev/null 2>&1 &

exit 0

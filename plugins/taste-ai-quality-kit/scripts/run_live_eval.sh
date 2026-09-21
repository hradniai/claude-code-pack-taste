#!/usr/bin/env bash
# Plugin-internal evaluator. It consumes the context .env but never prints values.
# Written for bash 3.2 (macOS default) as well as bash 5: no ${#array[@]} on a possibly empty array under set -u.
set -euo pipefail

context_dir="${TASTE_LLM_CONTEXT_DIR:-}"
prompt=""
intent=""
model=""
examples=""
judges=()
judge_count=0
judge_context=()
judge_context_count=0
isolation="auto"
tier=""
workspace="$PWD"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --context-dir) context_dir="${2:?missing context directory}"; shift 2 ;;
    --prompt) prompt="${2:?missing prompt path}"; shift 2 ;;
    --intent) intent="${2:?missing intent}"; shift 2 ;;
    --model) model="${2:?missing model}"; shift 2 ;;
    --tier) tier="${2:?missing tier}"; shift 2 ;;
    --examples) examples="${2:?missing examples path}"; shift 2 ;;
    --judge) judges+=("${2:?missing judge model}"); judge_count=$((judge_count + 1)); shift 2 ;;
    --judge-context) judge_context+=("${2:?missing judge context path}"); judge_context_count=$((judge_context_count + 1)); shift 2 ;;
    --isolation) isolation="${2:?missing isolation level}"; shift 2 ;;
    --workspace) workspace="${2:?missing workspace}"; shift 2 ;;
    *) echo "EVAL_NOT_CONFIGURED: unknown argument $1" >&2; exit 2 ;;
  esac
done
case "$isolation" in
  auto|namespace|sandboxed|config-only|environment) ;;
  *) echo "EVAL_NOT_CONFIGURED: isolation must be auto, namespace, sandboxed, config-only or environment" >&2; exit 10 ;;
esac

[ -n "$context_dir" ] || { echo "EVAL_NOT_CONFIGURED: evaluation context is not configured" >&2; exit 10; }
[ -n "$prompt" ] || { echo "EVAL_NOT_CONFIGURED: prompt is required" >&2; exit 10; }
[ -n "$intent" ] || { echo "EVAL_NOT_CONFIGURED: intent is required" >&2; exit 10; }
[ -n "$model" ] || { echo "EVAL_NOT_CONFIGURED: model is required" >&2; exit 10; }
[ "$tier" = "single-judge" ] || [ "$tier" = "jury" ] || { echo "EVAL_NOT_CONFIGURED: tier must be single-judge or jury" >&2; exit 10; }
[ "$judge_count" -gt 0 ] || { echo "EVAL_NOT_CONFIGURED: at least one judge model is required" >&2; exit 10; }
[ "$tier" != "jury" ] || [ "$judge_count" -ge 2 ] || { echo "EVAL_NOT_CONFIGURED: jury requires at least two judge models" >&2; exit 10; }
command -v python3 >/dev/null 2>&1 || { echo "EVAL_NOT_CONFIGURED: python3 is not installed on this computer" >&2; exit 10; }
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' || { echo "EVAL_NOT_CONFIGURED: python3 3.9 or newer is required" >&2; exit 10; }
if ! python3 "$(dirname "$0")/check_llm_context.py" --context-dir "$context_dir" >/dev/null; then
  echo "EVAL_NOT_CONFIGURED: evaluation context needs to be completed before the first run" >&2
  exit 10
fi
[ -f "$context_dir/.env" ] || { echo "EVAL_NOT_CONFIGURED: missing $context_dir/.env" >&2; exit 10; }
[ -f "$prompt" ] || { echo "EVAL_NOT_CONFIGURED: prompt file does not exist" >&2; exit 10; }
[ -d "$workspace" ] || { echo "EVAL_NOT_CONFIGURED: workspace does not exist" >&2; exit 10; }
[ -z "$examples" ] || [ -f "$examples" ] || { echo "EVAL_NOT_CONFIGURED: examples file does not exist" >&2; exit 10; }

# Read only the four known key names from the context .env. The file is parsed, never executed as shell
# code, so a stray `$(...)` or an unrelated variable in it cannot run anything or leak into the run.
load_key() {
  local name="$1" value
  # `|| true` keeps `set -e -o pipefail` quiet when the name is simply absent from the file.
  value=$({ grep -E "^[[:space:]]*(export[[:space:]]+)?${name}=" "$context_dir/.env" || true; } | tail -n 1 \
    | sed -E "s/^[[:space:]]*(export[[:space:]]+)?${name}=//; s/[[:space:]]+#.*$//; s/^[\"']//; s/[\"']?[[:space:]]*$//")
  if [ -n "$value" ]; then
    export "$name=$value"
  fi
  return 0
}
for key_name in GOOGLE_API_KEY GEMINI_API_KEY ANTHROPIC_API_KEY OPENAI_API_KEY; do
  load_key "$key_name"
done

if [ -z "${GOOGLE_API_KEY:-}" ] && [ -n "${GEMINI_API_KEY:-}" ]; then
  export GOOGLE_API_KEY="$GEMINI_API_KEY"
fi

require_key_for_model() {
  local provider="${1%%/*}"
  case "$provider" in
    google|gemini) [ -n "${GOOGLE_API_KEY:-}" ] || [ -n "${GEMINI_API_KEY:-}" ] ;;
    anthropic) [ -n "${ANTHROPIC_API_KEY:-}" ] ;;
    openai) [ -n "${OPENAI_API_KEY:-}" ] ;;
    claude-code|codex) return 0 ;;
    *) return 1 ;;
  esac
}

for configured_model in "$model" "${judges[@]}"; do
  require_key_for_model "$configured_model" || { echo "EVAL_NOT_CONFIGURED: a selected model has no configured provider key" >&2; exit 10; }
done

plugin_root=$(cd "$(dirname "$0")/.." && pwd)
runtime_home="${XDG_CACHE_HOME:-$HOME/.cache}/taste-ai-quality-kit/runtime"
requirements="$plugin_root/tools/prompt-eval/requirements.txt"
# The marker carries a checksum of requirements.txt: a plugin update that changes the runtime re-installs it.
ready_marker="$runtime_home/.ready-$(cksum "$requirements" | cut -d' ' -f1)"

# POSIX venv layout first, the Windows (Git Bash) layout second. Native Windows is not a supported target;
# the pack recommends WSL, where the POSIX layout applies.
resolve_python_bin() {
  if [ -x "$runtime_home/bin/python" ]; then
    python_bin="$runtime_home/bin/python"
  elif [ -x "$runtime_home/Scripts/python.exe" ]; then
    python_bin="$runtime_home/Scripts/python.exe"
  else
    python_bin=""
  fi
}
resolve_python_bin

# The marker is written only after a complete install, so a run interrupted mid-install is retried next time.
if [ -z "$python_bin" ] || [ ! -f "$ready_marker" ]; then
  mkdir -p "$runtime_home"
  python3 -m venv "$runtime_home" || { echo "EVAL_NOT_CONFIGURED: could not create the evaluation runtime (python3 -m venv failed)" >&2; exit 10; }
  resolve_python_bin
  [ -n "$python_bin" ] || { echo "EVAL_NOT_CONFIGURED: the evaluation runtime was created but its python was not found" >&2; exit 10; }
  "$python_bin" -m pip install --quiet --disable-pip-version-check -r "$requirements" \
    || { echo "EVAL_NOT_CONFIGURED: could not install the evaluation runtime (internet access is needed for this step)" >&2; exit 10; }
  : > "$ready_marker"
fi

args=(
  "$plugin_root/tools/prompt-eval/run_eval.py"
  --prompt "$prompt"
  --intent "$intent"
  --tier "$tier"
  --model "$model"
  --workspace "$workspace"
  --isolation "$isolation"
)
[ -n "$examples" ] && args+=(--examples "$examples")
for judge in "${judges[@]}"; do
  args+=(--judge "$judge")
done
if [ "$judge_context_count" -gt 0 ]; then
  for context_path in "${judge_context[@]}"; do
    args+=(--judge-context "$context_path")
  done
fi
exec "$python_bin" "${args[@]}"

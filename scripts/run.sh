#!/usr/bin/env bash
# Daily insights run. Cron entry point.
# Deliberately plain. macOS 26 XProtect killed an earlier version that wrapped
# everything in `exec > >(tee -a log) 2>&1` — a script hiding its output through
# a hidden subprocess while a child interpreter hits the network scores as C2.
# Log by redirecting in the cron line instead.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
# cron and launchd start with a bare PATH; both agent CLIs may live in ~/.local/bin
export PATH="$PATH:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin"

usage() {
  echo "Usage: $0 [--dry] [--inference codex|claude]"
}

DRY=0
INFERENCE=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry) DRY=1 ;;
    --inference)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --inference needs codex or claude" >&2
        usage >&2
        exit 2
      fi
      INFERENCE="$2"
      shift ;;
    --inference=*) INFERENCE="${1#--inference=}" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [ -z "$INFERENCE" ]; then
  INFERENCE="$(jq -er '.agent.inference' config.json)" || exit 1
fi
case "$INFERENCE" in
  codex|claude) ;;
  *) echo "ERROR: inference must be codex or claude: $INFERENCE" >&2; exit 2 ;;
esac
PROMPT_FILE="$(jq -er '.agent.prompt_file' config.json)" || exit 1
if [ ! -f "$PROMPT_FILE" ]; then
  echo "ERROR: prompt file not found: $PROMPT_FILE" >&2
  exit 1
fi
if ! command -v "$INFERENCE" >/dev/null 2>&1; then
  echo "ERROR: $INFERENCE is not on PATH" >&2
  exit 1
fi

# Keep inference credentials out of the fetch, notification, and build steps.
if [ -f .env ]; then set -a; . ./.env; set +a; fi
CODEX_KEY="${CODEX_API_KEY:-}"
CLAUDE_KEY="${ANTHROPIC_API_KEY:-}"
unset CODEX_API_KEY ANTHROPIC_API_KEY
echo "=== run $(date -u +%FT%TZ) dry=$DRY inference=$INFERENCE"

python3 scripts/fetch.py || echo "WARN: fetch had failures, continuing"

# Both CLIs stream JSON events, with different event shapes. Keep one progress
# line per tool call so terminal and cron runs remain watchable.
if [ "$INFERENCE" = "claude" ]; then
  TOOLS="$(jq -er '.agent.claude_allowed_tools | join(",")' config.json)" || exit 1
  ( if [ -n "$CLAUDE_KEY" ]; then export ANTHROPIC_API_KEY="$CLAUDE_KEY"; fi
    claude -p "$(cat "$PROMPT_FILE")" \
      --allowedTools "$TOOLS" \
      --permission-mode acceptEdits \
      --verbose --output-format stream-json
  ) \
    | jq -r --unbuffered '
        if .type=="system" and .subtype=="init" then "agent session \(.session_id)"
        elif .type=="assistant" then (.message.content[]? | select(.type=="tool_use")
          | "  \(.name)  \((.input.url // .input.file_path // .input.command // "") | .[0:100])")
        elif .type=="result" then
          if .subtype=="success" then "agent done: \(.subtype)  turns=\(.num_turns // "?")  cost=$\(.total_cost_usd // "?")"
          else error("claude result: \(.subtype // "unknown")") end
        else empty end' \
    || { echo "ERROR: claude run failed"; exit 1; }
else
  CODEX_MODEL="$(jq -er '.agent.codex_model' config.json)" || exit 1
  CODEX_REASONING="$(jq -ce '.agent.codex_reasoning_effort' config.json)" || exit 1
  CODEX_ARGS=(--json)
  VAULT_DIR="$(python3 -c 'import json, os; print(os.path.realpath(json.load(open("config.json"))["paths"]["vault_dir"]))')" || exit 1
  case "$VAULT_DIR" in
    "$PWD"|"$PWD"/*) ;;
    *) mkdir -p "$VAULT_DIR" || exit 1; CODEX_ARGS=(--add-dir "$VAULT_DIR" --json) ;;
  esac
  ( if [ -n "$CODEX_KEY" ]; then export CODEX_API_KEY="$CODEX_KEY"; fi
    codex -a never --search --disable plugins --disable apps exec \
      --ignore-user-config --sandbox workspace-write \
      --model "$CODEX_MODEL" -c "model_reasoning_effort=$CODEX_REASONING" \
      "${CODEX_ARGS[@]}" - < "$PROMPT_FILE"
  ) \
    | python3 scripts/codex_progress.py \
    || { echo "ERROR: codex run failed"; exit 1; }
fi

if [ "$DRY" -eq 1 ]; then
  echo "dry run, skipping push"
else
  python3 scripts/notify.py || echo "WARN: telegram push failed"
fi

# The site is a static projection of digests/*.json. Built last, on purpose:
# it must never delay or fail the push, which is the routine's actual job.
WEB="$(python3 -c 'import json;c=json.load(open("config.json")).get("web",{});print(c.get("dir","") if c.get("build_on_run") else "")')"
if [ -n "$WEB" ]; then
  if command -v npm >/dev/null 2>&1; then
    echo "=== web build"
    ( cd "$WEB" && { [ -d node_modules ] || npm ci; } && npm run build ) || echo "WARN: web build failed"
  else
    echo "WARN: web.build_on_run is on but npm is not on PATH"
  fi
fi
echo "=== done $(date -u +%FT%TZ)"

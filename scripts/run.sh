#!/usr/bin/env bash
# Daily insights run. Cron entry point.
# Deliberately plain. macOS 26 XProtect killed an earlier version that wrapped
# everything in `exec > >(tee -a log) 2>&1` — a script hiding its output through
# a hidden subprocess while a child interpreter hits the network scores as C2.
# Log by redirecting in the cron line instead.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
# cron and launchd start with a bare PATH; claude lives in ~/.local/bin
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
# headless box: claude authenticates via ANTHROPIC_API_KEY from .env
if [ -f .env ]; then set -a; . ./.env; set +a; fi

DRY=0
[ "${1:-}" = "--dry" ] && DRY=1
echo "=== run $(date -u +%FT%TZ) dry=$DRY"

python3 scripts/fetch.py || echo "WARN: fetch had failures, continuing"

TOOLS="$(python3 -c 'import json;print(",".join(json.load(open("config.json"))["agent"]["allowed_tools"]))')"
# stream-json + jq: one line per tool call as it happens, so a silent 5-minute
# headless run is watchable in the terminal or via `tail -f state/run.log`.
claude -p "$(cat prompts/daily_scan.md)" \
  --allowedTools "$TOOLS" \
  --permission-mode acceptEdits \
  --verbose --output-format stream-json \
  | jq -r --unbuffered '
      if .type=="system" and .subtype=="init" then "agent session \(.session_id)"
      elif .type=="assistant" then (.message.content[]? | select(.type=="tool_use")
        | "  \(.name)  \((.input.url // .input.file_path // .input.command // "") | .[0:100])")
      elif .type=="result" then "agent done: \(.subtype // "?")  turns=\(.num_turns // "?")  cost=$\(.total_cost_usd // "?")"
      else empty end' \
  || { echo "ERROR: agent run failed"; exit 1; }

if [ "$DRY" -eq 1 ]; then
  echo "dry run, skipping push"
else
  python3 scripts/notify.py || echo "WARN: telegram push failed"
fi
echo "=== done $(date -u +%FT%TZ)"

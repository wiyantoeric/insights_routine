#!/usr/bin/env bash
# Delivery smoke test.
#   scripts/chat.sh --platform telegram "hi there"
#   scripts/chat.sh --platform telegram --file digests/2026-09-05.md
set -euo pipefail
cd "$(dirname "$0")/.."
PLATFORM=telegram FILE=
while [ $# -gt 0 ]; do
  case "$1" in
    --platform) PLATFORM="$2"; shift 2 ;;
    --file)     FILE="$2"; shift 2 ;;
    *) break ;;
  esac
done
if [ -n "$FILE" ]; then
  [ -f "$FILE" ] || { echo "no such file: $FILE" >&2; exit 2; }
  exec python3 scripts/notify.py --platform "$PLATFORM" "$FILE"
fi
[ $# -ge 1 ] || { echo "usage: $0 [--platform telegram] (--file path.md | \"message\")" >&2; exit 2; }
exec python3 scripts/notify.py --platform "$PLATFORM" --text "$*"

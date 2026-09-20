"""Render Codex JSONL progress and require a completed turn."""

import json
import sys


TOOL_TYPES = {"web_search", "command_execution", "file_change", "mcp_tool_call"}


def detail(item):
    changes = item.get("changes") or []
    path = changes[0].get("path", "") if changes else ""
    value = item.get("query") or item.get("command") or item.get("name") or path
    return " ".join(str(value).split())[:100]


def main():
    completed = False
    failed = False
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"ERROR: invalid Codex event: {exc}", file=sys.stderr)
            return 1

        kind = event.get("type")
        item = event.get("item") or {}
        if kind == "thread.started":
            print(f"agent session {event.get('thread_id', '?')}", flush=True)
        elif kind == "item.completed" and item.get("type") in TOOL_TYPES:
            print(f"  {item['type']}  {detail(item)}", flush=True)
        elif kind == "item.completed" and item.get("type") == "error":
            print(f"agent warning: {item.get('message', 'unknown')}", flush=True)
        elif kind == "error":
            # Codex also emits this for recoverable reconnect attempts.
            print(f"agent notice: {event.get('message', 'unknown')}", flush=True)
        elif kind == "turn.failed":
            failed = True
            error = event.get("error") or {}
            print(f"agent error: {error.get('message', 'unknown')}", flush=True)
        elif kind == "turn.completed":
            completed = True
            usage = event.get("usage") or {}
            print(
                "agent done: input_tokens={}  output_tokens={}".format(
                    usage.get("input_tokens", "?"), usage.get("output_tokens", "?")
                ),
                flush=True,
            )

    if failed or not completed:
        print("ERROR: Codex ended without a successful turn", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

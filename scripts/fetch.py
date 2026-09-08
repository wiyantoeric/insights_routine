#!/usr/bin/env python3
"""Ingestion orchestrator: run every enabled source in sources/, write state/candidates.json.

Knows nothing about any particular site or API. Add a source by adding a file
to sources/, not by editing this. One source failing never aborts the run.
"""
import json, os, sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import config, registry
from core.items import load_seen


def interleave(items, cap):
    """Round-robin across sources, newest first within each, so one source that
    bulk-touched its lastmod cannot push every other source out of the window."""
    by_src = {}
    for i in sorted(items, key=lambda i: i["lastmod"], reverse=True):
        by_src.setdefault(i["source"], []).append(i)
    out = []
    while len(out) < cap and any(by_src.values()):
        for src in list(by_src):
            if by_src[src]:
                out.append(by_src[src].pop(0))
                if len(out) >= cap:
                    break
    return out


def main():
    cfg = config.load()
    config.load_env()
    now = datetime.now(timezone.utc)
    ctx = SimpleNamespace(
        cfg=cfg, now=now,
        cutoff=now - timedelta(days=cfg["run"]["lookback_days"]),
        seen=load_seen(config.path(cfg, "seen")),
    )
    candidates, tape, errors = [], {}, []

    for spec in registry.load_specs():
        if not spec["enabled"]:
            continue
        try:
            result, errs = registry.run(spec, ctx)
            errors.extend(errs)
        except Exception as e:
            errors.append({"source": spec["id"], "error": str(e)})
            print("%-10s FAILED %s" % (spec["id"], e), file=sys.stderr)
            continue
        if spec["role"] == "content":
            candidates.extend(result)
            print("%-10s %3d new" % (spec["id"], len(result)), file=sys.stderr)
        else:
            tape[spec["id"]] = result
            print("%-10s %3d readings" % (spec["id"], len(result)), file=sys.stderr)

    candidates = interleave(candidates, cfg["run"]["max_candidates_to_agent"])

    payload = {
        "generated_at": now.isoformat(),
        "lookback_days": cfg["run"]["lookback_days"],
        "candidate_count": len(candidates),
        "candidates": candidates,
        "tape": tape,
        "errors": errors,
    }
    out = config.path(cfg, "candidates")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(payload, f, indent=2)
    print("wrote %s: %d candidates, %d errors" % (out, len(candidates), len(errors)), file=sys.stderr)


def demo():
    """Self-check for the parsing that is easy to get silently wrong."""
    from core.sitemap import parse_lastmod, parse_sitemap
    from core.items import title_from_url, url_id
    assert parse_lastmod("2026-07-23T23:04Z").year == 2026, "PwC minute-precision form"
    assert parse_lastmod("2026-07-23T23:04:11+07:00").tzinfo is not None, "offset form"
    assert parse_lastmod("2026-07-23") is not None, "date-only form"
    assert parse_lastmod(None) is None and parse_lastmod("garbage") is None
    entries = parse_sitemap(b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                            b'<url><loc>https://x/a.html</loc><lastmod>2026-01-02T03:04Z</lastmod></url></urlset>')
    assert entries == [("https://x/a.html", "2026-01-02T03:04Z")], entries
    assert title_from_url("https://x/y/ai-in-banking-2026.html") == "Ai In Banking 2026"
    assert url_id("https://x") == url_id("https://x") and len(url_id("https://x")) == 16
    items = [{"source": s, "lastmod": str(n)} for s in "abc" for n in range(5)] + [{"source": "z", "lastmod": "9"}]
    picked = interleave(items, 5)
    assert [i["source"] for i in picked] == ["z", "a", "b", "c", "a"], picked  # source order = its newest item
    specs = registry.load_specs()
    assert {s["id"] for s in specs} >= {"kpmg", "deloitte", "pwc", "crypto", "quotes", "macro"}, specs
    for s in specs:  # every non-builtin kind must resolve to a module with fetch()
        if s["kind"] not in registry.BUILTIN:
            assert callable(registry._module(s["kind"]).fetch), s["kind"]
    print("demo ok: %d sources registered" % len(specs))


if __name__ == "__main__":
    demo() if "--demo" in sys.argv else main()

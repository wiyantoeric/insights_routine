#!/usr/bin/env python3
"""Push a digest to Telegram. Long form stays in the vault; this is the short form.

    notify.py                       newest digest
    notify.py digests/2026-09-05.md that digest
    notify.py --text "hi there"     ad-hoc message, delivery smoke test
"""
import argparse, json, os, re, sys, urllib.request, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import ROOT, load_env


def chunks(text, limit):
    """Split on blank lines, never mid-item, hard-split only if one item exceeds limit."""
    out, buf = [], ""
    for block in text.split("\n\n"):
        while len(block) > limit:
            out.append(block[:limit])
            block = block[limit:]
        if len(buf) + len(block) + 2 > limit:
            if buf:
                out.append(buf)
            buf = block
        else:
            buf = buf + "\n\n" + block if buf else block
    if buf:
        out.append(buf)
    return out


def send(token, chat_id, text, parse_mode):
    data = urllib.parse.urlencode({
        "chat_id": chat_id, "text": text,
        "parse_mode": parse_mode, "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request("https://api.telegram.org/bot%s/sendMessage" % token, data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("digest", nargs="?", help="digest file; default newest in digests/")
    ap.add_argument("--text", help="send this text instead of a digest")
    ap.add_argument("--platform", default="telegram", help="key under delivery in config.json")
    a = ap.parse_args()

    load_env()
    with open(os.path.join(ROOT, "config.json")) as f:
        c = json.load(f)
    if a.platform != "telegram":
        sys.exit("platform %r not implemented; only telegram" % a.platform)
    tg = c["delivery"]["telegram"]
    if not tg["enabled"]:
        sys.exit("telegram disabled in config.json delivery.telegram.enabled")
    token = os.environ.get(tg["token_env"], "")
    chat_id = os.environ.get(tg["chat_id_env"], "")
    if not token or not chat_id:
        sys.exit("missing %s / %s — see .env.example" % (tg["token_env"], tg["chat_id_env"]))

    if a.text is not None:
        send(token, chat_id, a.text, tg["parse_mode"])
        print("sent", file=sys.stderr)
        return

    src = a.digest
    if not src:
        d = os.path.join(ROOT, c["paths"]["digest_dir"])
        files = sorted(f for f in os.listdir(d) if f.endswith(".md"))
        if not files:
            sys.exit("no digest found in %s" % d)
        src = os.path.join(d, files[-1])
    with open(src) as f:
        body = f.read()

    # strip obsidian frontmatter and wikilink brackets, telegram renders neither
    body = re.sub(r"\A---\n.*?\n---\n", "", body, flags=re.S)
    body = re.sub(r"\[\[([^\]]+)\]\]", r"\1", body)

    for i, part in enumerate(chunks(body, tg["max_chars"]), 1):
        try:
            send(token, chat_id, part, tg["parse_mode"])
        except Exception:
            send(token, chat_id, part, "")  # markdown parse errors: resend plain
        print("sent chunk %d" % i, file=sys.stderr)


def demo():
    long_block = "x" * 250
    parts = chunks("a\n\nb\n\n" + long_block, 100)
    assert all(len(p) <= 100 for p in parts), [len(p) for p in parts]
    assert "".join(p.replace("\n", "") for p in parts).count("x") == 250
    assert chunks("short", 100) == ["short"]
    assert re.sub(r"\[\[([^\]]+)\]\]", r"\1", "see [[agentic ai]]") == "see agentic ai"
    print("demo ok")


if __name__ == "__main__":
    demo() if "--demo" in sys.argv else main()

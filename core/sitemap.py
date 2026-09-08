"""Sitemap-index sources. Declarative: a sources/<id>.json with kind=sitemap needs no code."""
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from core.http import get
from core.items import item, fresh_unseen


def _strip_ns(tag):
    return tag.rsplit("}", 1)[-1]


def parse_sitemap(raw):
    """[(loc, lastmod_or_None)] from either a sitemapindex or a urlset."""
    out = []
    for node in ET.fromstring(raw):
        loc = mod = None
        for child in node:
            t = _strip_ns(child.tag)
            if t == "loc":
                loc = (child.text or "").strip()
            elif t == "lastmod":
                mod = (child.text or "").strip()
        if loc:
            out.append((loc, mod))
    return out


_FORMATS = (
    "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M%z",
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d",
)


def parse_lastmod(s):
    """Tolerant: PwC emits minute precision with a bare Z, Deloitte omits it entirely."""
    if not s:
        return None
    s = s.strip().replace("Z", "+0000")
    s = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", s)
    s = re.sub(r"\.\d+", "", s)
    for fmt in _FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def collect(spec, ctx):
    """index -> shards matching child_match -> fresh, on-path, unseen URLs.
    Returns (items, errors). One dead shard never kills the source."""
    index = parse_sitemap(get(spec["index"]))
    shards = [loc for loc, _ in index if any(m in loc for m in spec.get("child_match", []))]
    if not shards:  # flat sitemap, not an index
        shards = [spec["index"]]
    include = [p.lower() for p in spec.get("include_path", [])]
    exclude = [p.lower() for p in spec.get("exclude_path", [])]
    items, errors = [], []
    for shard in shards:
        try:
            entries = parse_sitemap(get(shard))
        except Exception as e:
            errors.append({"source": spec["id"], "shard": shard, "error": str(e)})
            continue
        for loc, mod in entries:
            dt = parse_lastmod(mod)
            if dt is None or dt < ctx.cutoff:
                continue
            low = loc.lower()
            if include and not any(p in low for p in include):
                continue
            if any(p in low for p in exclude):
                continue
            items.append(item(spec, loc, dt))
    return fresh_unseen(items, ctx.seen, spec.get("max_urls", 400)), errors

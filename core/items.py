"""The candidate item shape and the helpers every content source needs."""
import hashlib, json, re


def url_id(url):
    """16-char SHA1. The key in state/seen.json."""
    return hashlib.sha1(url.encode()).hexdigest()[:16]


def title_from_url(url):
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    slug = re.sub(r"\.(html?|aspx|pdf)$", "", slug)
    return re.sub(r"[-_]+", " ", slug).strip().title()


def load_seen(path):
    try:
        with open(path) as f:
            return set(json.load(f).get("ids", []))
    except (IOError, ValueError):
        return set()


def item(spec, url, dt, title=None):
    """Build one candidate. Every content source returns a list of these."""
    return {
        "id": url_id(url),
        "source": spec["id"],
        "source_name": spec.get("name", spec["id"]),
        "url": url,
        "lastmod": dt.isoformat(),
        "title_guess": title or title_from_url(url),
    }


def fresh_unseen(items, seen, cap):
    """Newest first, deduped by id, not in seen, capped."""
    items.sort(key=lambda i: i["lastmod"], reverse=True)
    out, taken = [], set()
    for i in items:
        if i["id"] in seen or i["id"] in taken:
            continue
        taken.add(i["id"])
        out.append(i)
    return out[:cap]

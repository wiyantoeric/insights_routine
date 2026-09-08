# SOURCES.md — registry, contract, field notes

Every source is one file in `sources/`. `scripts/fetch.py` knows nothing about
any site; it discovers `sources/*.json` and dispatches each to its
implementation. Add a source by adding a file, not by editing the orchestrator.

## The contract

`sources/<id>.json`:

```json
{
  "id": "kpmg",            // optional, defaults to filename
  "name": "KPMG",          // display name on items
  "role": "content",       // "content" -> candidate items   |   "tape" -> market readings
  "kind": "sitemap",       // "sitemap" is built in; anything else names sources/<kind>.py
  "enabled": true,         // default true
  ...                      // whatever the implementation reads
}
```

`sources/<kind>.py` when the kind is not built in:

```python
def fetch(spec, ctx):
    """spec = the JSON above. ctx has .cfg .cutoff .seen .now
    content role: return (list_of_items, errors)   items via core.items.item()
    tape role:    return (dict_of_readings, errors)
    Raise for a total failure; return partial results + errors for a partial one."""
```

Reusable pieces in `core/` — use these, do not re-implement:

| Import | Gives |
|---|---|
| `core.http.get(url)` | GET with browser UA, gzip, one retry. Yahoo needs this UA |
| `core.sitemap.parse_sitemap(bytes)` | `[(loc, lastmod)]` from index or urlset |
| `core.sitemap.parse_lastmod(str)` | tolerant ISO parse, `None` on garbage |
| `core.items.item(spec, url, dt, title=None)` | one candidate in the shape the agent expects |
| `core.items.fresh_unseen(items, seen, cap)` | newest first, dedup by id, drop seen, cap |
| `core.items.url_id(url)` | the `seen.json` key |
| `core.config.load() / path() / load_env()` | config, absolute paths, `.env` |

## Adding a source

**Sitemap site** — JSON only. Find the index in the site's `robots.txt`
(`Sitemap:` line), copy `sources/pwc.json`, set `index`, `child_match`,
`include_path`, `exclude_path`. Run `python3 scripts/fetch.py`, read the
per-source count on stderr, note quirks below.

**Anything else** (RSS, JSON API, press-release page, another price feed) —
one JSON spec plus one `sources/<kind>.py` with `fetch()`. Copy
`sources/yahoo.py` for a tape source or write a `content` one that returns
`core.items.item(...)` dicts through `fresh_unseen()`. Run
`python3 scripts/fetch.py --demo`; it asserts every kind resolves to a module
with `fetch`.

A kind is reusable: one `rss.py` serves every RSS spec, the way `sitemap`
serves three firms today.

## Registered today

| File | Role | Kind | Notes |
|---|---|---|---|
| `kpmg.json` | content | sitemap | `xx/en` global + `id sg uk us` shards |
| `deloitte.json` | content | sitemap | global, us, uk, in shards. **No SEA shard exists** |
| `pwc.json` | content | sitemap | gx, us, id, sg shards |
| `crypto.json` + `coingecko.py` | tape | coingecko | BTC ETH SOL, USD, 24h change |
| `quotes.json` + `yahoo.py` | tape | yahoo | 8 tickers, 1d change, z-score, alert flag |
| `macro.json` + `fred.py` | tape | fred | **disabled** until `FRED_API_KEY` is in `.env` |

Ingestion is hybrid on purpose: sitemaps carry `lastmod`, which is all "what is
new since yesterday" needs, at one request per shard. The JS-rendered landing
pages the operator originally bookmarked are in `config.json → agent.context_pages`
for the agent to WebFetch when an item needs context; they are not ingestion.

## Per-firm field notes (verified 2026-09-05)

### KPMG
- robots.txt → `https://kpmg.com/sitemap-index.xml` — 169 shards, `kpmg.com/{cc}/{lang}/sitemap.xml`
- SEA shards present: `id/en`, `sg/en`, `my/en`, `th/en`, `vn/en`, `vn/vi`
- `xx/en` global shard: 5,182 URLs, `lastmod` on 100%
- Root `kpmg.com/sitemap.xml` is a 404 HTML page. Use the index only.

### Deloitte
- robots.txt → `https://www.deloitte.com/sitemap_index.xml` — 82 shards, `sitemap_{cc}_en.xml`
- Global shard: 3,140 URLs, `lastmod` on ~87%. Missing `lastmod` = unknown, skipped.
- **No `sea`, `id`, `sg`, `my`, `th` shard.** SEA content surfaces under `global`.
- `www2.deloitte.com` is the legacy host. No RSS at any tried path.
- **Bulk `lastmod` bumps.** 2026-09-07 (a Sunday) touched 33+ hub pages
  (`/insights/industry/private-capital.html`, research-center indexes, etc.)
  with no new content. `fetch.py` round-robins across sources so this cannot
  starve KPMG/PwC; triage drops the hubs by title. If it recurs weekly, add
  hub paths to `exclude_path`.

### PwC
- robots.txt → `https://www.pwc.com/sitemap.xml` — 107 shards, `pwc.com/{cc}/{lang}/sitemaps/sitemap1.xml`
- SEA present: `id/en`, `sg/en`, `my/en`, `th/en`, `vn/en`, `vn/vn`
- `lastmod` minute precision, bare `Z`, no seconds. `parse_lastmod` handles it.
- No RSS. `gx` article pages sometimes 403 on fetch (seen 2026-09-05).

## Market endpoints

| Kind | Endpoint | Notes |
|---|---|---|
| coingecko | `api.coingecko.com/api/v3/simple/price` | free, no key, ~10-30 req/min, one call for all ids |
| yahoo | `query1.finance.yahoo.com/v8/finance/chart/{sym}` | needs browser UA. `^JKSE` confirmed. `^TNX` reads the yield directly (4.78 = 4.78%) |
| fred | `api.stlouisfed.org/fred/series/observations` | free key required |

## Candidate additions

Not wired. One at a time, after the base loop is stable.

- McKinsey, BCG, Bain, EY — sitemap kind, JSON only. Doubles cross-firm confirmation.
- OJK, Bank Indonesia press rooms — probably a new `content` kind. The local regulatory-deadline feed, direct input to Lens A.
- IMF / World Bank / BIS — macro, and a non-vendor check on consulting claims.
- ASEAN Briefing, Tech in Asia — the SEA lag signal in Lens D. Likely `rss` kind.

## Failure log

Date, symptom, fix. Append.

- **2026-09-05** — `./scripts/run.sh --dry` killed by macOS 26.6.2 XProtect ("Malicious Script Blocked") ~8s in, during market calls. Static YARA has no matching rule; behavioral signature `macOS.Network.Outgoing` (BastionRule-21) fires for `python3`/`bash`/`curl` outbound. Suspected combo: `exec > >(tee)` hidden-output redirect + child interpreter bursting ~22 connections to 6 hosts. Fix: removed the wrapper, log via cron redirect. Passed on re-run.
- **2026-09-08** — Deloitte returned 400 candidates (cap) after a site-wide `lastmod` bump on 2026-09-07; global newest-first cut left zero KPMG/PwC items. Fix: `fetch.py::interleave()` round-robins by source. Note added above.

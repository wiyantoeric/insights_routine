# ARCHITECTURE.md — where to look, and what already exists

Two questions this file answers. "I want to do X, which file?" and "do we
already have Y?" If the answer to the second is yes, reuse it.

## The shape

```
cron ──► scripts/run.sh
            │
            ├─ 1. python3 scripts/fetch.py            deterministic, ~15s, no LLM
            │       for each sources/*.json (enabled):
            │         kind=sitemap  ──► core/sitemap.collect()     ─┐ role=content ──► candidates[]
            │         kind=<other>  ──► sources/<kind>.py fetch()  ─┘ role=tape    ──► tape{id}
            │       interleave by source, cap ──► state/candidates.json
            │
            ├─ 2. claude -p prompts/daily_scan.md       the agent, 3-6 min
            │       reads: config.json, docs/RULES.md, docs/OPPORTUNITIES.md, docs/WORKFLOWS.md, candidates.json
            │       does:  triage ──► WebFetch survivors ──► score ──► write
            │       writes: digests/YYYY-MM-DD.md, <vault_dir>/YYYY-MM/YYYY-MM-DD.md, state/seen.json
            │
            └─ 3. python3 scripts/notify.py             chunk + POST to Telegram

core/        shared, reusable: http, sitemap, items, config, registry
sources/     one file per source: <id>.json spec, optional <kind>.py implementation
config.json  run behaviour only. Not sources. Read by everything, written by nothing.
```

## Where to look when doing something

| I want to… | Go to | Not there |
|---|---|---|
| Add a firm or regulator that has a sitemap | new `sources/<id>.json`, `kind: sitemap` | no code |
| Add a source that is RSS, an API, a scraped page | `sources/<id>.json` + `sources/<kind>.py` with `fetch()` | not `scripts/fetch.py` |
| Add a ticker, coin, or FRED series | `sources/quotes.json`, `sources/crypto.json`, `sources/macro.json` | no code |
| Turn FRED on | `FRED_API_KEY` in `.env`, `enabled: true` in `sources/macro.json` | code exists: `sources/fred.py` |
| Disable a source for a while | `"enabled": false` in its spec | do not delete the file |
| Change a regional shard or a path filter | that source's `child_match` / `include_path` / `exclude_path` | |
| Change the price-alert threshold | `sources/quotes.json → alert_sigma` | |
| Change what counts as an opportunity, or how items are scored | `docs/OPPORTUNITIES.md` | not the prompt |
| Change scoring weights or the publish threshold | `config.json → scoring` | `OPPORTUNITIES.md` documents, config decides |
| Change what the agent does step by step | `docs/WORKFLOWS.md` § W1, then `prompts/daily_scan.md` if the prompt must change | |
| Change the digest layout | `docs/WORKFLOWS.md → Digest shape` | not the prompt |
| Add a hard rule for the agent | `docs/RULES.md` | |
| Change lookback, item cap, fetch budget, candidate cap | `config.json → run` | |
| Change theme / geography focus / mute terms | `config.json → focus` | |
| Change output paths | `config.json → paths` | |
| Add Slack or another push target | `scripts/notify.py`: branch on `a.platform`, read `delivery.<name>` | `chat.sh` needs nothing |
| Change Telegram chunking | `config.json → delivery.telegram`; logic is `notify.py::chunks()` | |
| Debug why a URL was not picked up | `python3 scripts/fetch.py`, read `state/candidates.json`; check `lastmod` vs lookback, then path filters, then `seen.json`, then whether interleave cut it | |
| Debug why the agent scored something a certain way | `claude -r <session-id>` (first line `run.sh` prints) | |
| Force a full re-scan | empty `ids` in `state/seen.json` | |
| Test delivery alone | `scripts/chat.sh --platform telegram "hi"` or `--file <md>` | |
| Add a second routine (weekly synthesis…) | new section in `docs/WORKFLOWS.md`, new `prompts/` file, new `config.json` block, new cron line | do not fork `run.sh` |
| Record that a source broke | `docs/SOURCES.md → Failure log` | |
| Onboard a human / an agent | `README.md` / `AGENTS.md` | |

Rule of thumb: **spec before config, config before prompt, prompt before code.**
A new source is a JSON file. A new *kind* of source is a Python file next to it.
`scripts/fetch.py` is never the answer.

## Yes, we already have this

### Layout

| Path | Is |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | agent entry and routing |
| `docs/` | RULES, WORKFLOWS, OPPORTUNITIES, SOURCES, ARCHITECTURE |
| `README.md` | human getting-started |
| `config.json` | `run`, `paths`, `focus`, `scoring`, `delivery`, `agent` |
| `.env` / `.env.example` | secrets. `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, optional `FRED_API_KEY` |
| `prompts/daily_scan.md` | the executed prompt; points at docs, does not repeat them |
| `core/` | shared library, below |
| `sources/` | one spec per source, plus implementations for non-builtin kinds |
| `scripts/run.sh` | orchestrator. fetch → agent → notify. `--dry`. Streams agent tool calls |
| `scripts/fetch.py` | source-agnostic ingestion loop + `interleave()`. `--demo` |
| `scripts/notify.py` | Telegram. positional digest, `--text`, `--platform`. `--demo` |
| `scripts/chat.sh` | delivery smoke test wrapper |
| `state/seen.json` | `{"ids":[…]}` published URL hashes. Agent appends |
| `state/candidates.json` | per-run payload: `candidates[]`, `tape{}`, `errors[]` |
| `digests/`, `vaults/` | outputs. Gitignored |

### `core/` — reuse these

| Module | Function | Does |
|---|---|---|
| `config` | `ROOT` | repo root, derived from file location |
| | `load()` | `config.json` as dict |
| | `path(cfg, key)` | `paths.<key>` made absolute |
| | `load_env()` | `.env` into `os.environ`, no override |
| `http` | `get(url, timeout, retries)` | GET, browser UA, gzip, one retry |
| `sitemap` | `parse_sitemap(bytes)` | `[(loc, lastmod)]`, index or urlset, namespace-agnostic |
| | `parse_lastmod(str)` | tolerant ISO → aware datetime, or `None` |
| | `collect(spec, ctx)` | the built-in `sitemap` kind, end to end |
| `items` | `url_id(url)` | 16-char SHA1, the seen key |
| | `title_from_url(url)` | slug → Title Case |
| | `load_seen(path)` | set of ids |
| | `item(spec, url, dt, title)` | one candidate in the agreed shape |
| | `fresh_unseen(items, seen, cap)` | sort, dedup, drop seen, cap |
| `registry` | `load_specs()` | every `sources/*.json`, validated, defaults applied |
| | `run(spec, ctx)` | dispatch to builtin or `sources/<kind>.py` |
| | `BUILTIN` | `{"sitemap": …}`; add a built-in kind here |

### `sources/` — kinds available

| Kind | Where | Serves |
|---|---|---|
| `sitemap` | `core/sitemap.py` (built in) | any site with a sitemap index. Three firms today |
| `coingecko` | `sources/coingecko.py` | any coin CoinGecko lists |
| `yahoo` | `sources/yahoo.py` | any Yahoo ticker: equities, indexes, FX, futures, yields |
| `fred` | `sources/fred.py` | any FRED series |

### Behaviours already handled

- **Source discovery** — drop a JSON in `sources/`, it runs. No registration step.
- **Per-source isolation** — one source raising lands in `errors[]`, the rest run.
- **Per-shard isolation** — inside a sitemap source, a dead shard is skipped, not fatal.
- **Fair truncation** — `interleave()` round-robins by source before the candidate cap, so a bulk `lastmod` bump on one site cannot starve the others.
- **Dedup across runs** — `seen.json`, published items only; triaged-away items can resurface.
- **Dedup within a run** — same URL in two shards collapses.
- **Missing `lastmod`** — skipped as unknown, never treated as new.
- **Telegram 4096 limit, Markdown parse failure, frontmatter and wikilink stripping** — `notify.py`.
- **Price outliers** — z-score over the window, `alert: true` above `alert_sigma`.
- **Zero-item day** — valid; rules forbid padding.
- **Live progress for a headless run** — `run.sh` streams tool calls; session id first.
- **macOS XProtect** — `run.sh` avoids the `exec > >(tee)` shape. See `docs/SOURCES.md` failure log.

### Not built, on purpose

| Thing | Why not yet | Add when |
|---|---|---|
| `rss` kind | no RSS source registered | first RSS spec. One `sources/rss.py` then serves all of them |
| Rolling-URL handling (same URL, new content weekly) | one such URL so far; agent skips hashing it | a second appears. Then `"rolling": true` per spec, hash `url + lastmod` |
| Per-source hub-page exclusion for Deloitte | one bump seen | it recurs. Then `exclude_path` entries |
| Weekly synthesis routine | daily not yet proven over a month | four weeks of digests exist |
| Slack / email delivery | Telegram chosen | someone else needs the feed |
| More firms / regulators | base loop first | one at a time, JSON only for sitemap sites |
| Retry queue for 403s | one so far | it repeats |
| Tests beyond `--demo` | asserts cover the parsers, interleave, and registry resolution | logic outgrows one `demo()` |
| Python deps, venv, uv | system 3.9 + stdlib suffices | stdlib stops being enough |

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
            │       writes: digests/YYYY-MM-DD.{md,json}, <vault_dir>/YYYY-MM/YYYY-MM-DD.md, state/seen.json
            │              formats gated by delivery.digest_archive.formats
            │
            ├─ 3. python3 scripts/notify.py             chunk + POST to Telegram
            │
            └─ 4. npm run build  (in web.dir)           static site, ~1s, optional
                    app/scripts/collect.mjs reads digests/*.json ──► app/src/lib/data/
                    SvelteKit prerenders one page per digest, topic and view ──► app/build/
                    skipped unless web.build_on_run; failure warns, never fails the run

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
| Stop writing markdown or json digests | `config.json → delivery.digest_archive.formats` | not the prompt |
| Change the sidecar json schema | `docs/WORKFLOWS.md → Sidecar JSON`, then `prompts/daily_scan.md` | not the reader |
| Change what the site shows on a page | `app/src/routes/…` | |
| Write or change any text on the site | `docs/ARCHITECTURE.md → Site copy`, then the route | |
| Change how search matches or ranks | `app/src/lib/Results.svelte`; the field and shortcuts are `Finder.svelte` | not a route |
| Change how digest markdown renders | `app/src/lib/md.js`: `md()` is inline only, `mdDoc()` adds blocks. Asserts in `app/scripts/md.check.mjs` | not the components |
| Change how the agent writes the long fields | `docs/WORKFLOWS.md → Writing the long fields`, then `prompts/daily_scan.md` | not the renderer |
| Change how a reference or footnote looks | `app/src/lib/md.js` for the marker, `Entry.svelte` for the numbered source list | |
| Change the tape shape | `docs/WORKFLOWS.md → Sidecar JSON`, then `app/src/lib/Tape.svelte` | `collect.mjs` normalises the old string form |
| Add a filter to the finder | `app/scripts/collect.mjs` to carry the field, then `Filters.svelte` | |
| Change colours, type scale, or the visual rules | `DESIGN.md` first, then `app/src/app.css` | tokens, not literals |
| Change the favicon | replace `app/static/favicon.jpg` | not an import; small files imported from `src/` get inlined as base64 into every page |
| Add or restyle a colour theme | the `:root[data-theme='…']` blocks in `app/src/app.css`, then the swatch list in `app/src/lib/ThemeToggle.svelte` | |
| Change what data reaches the site at all | `app/scripts/collect.mjs` | not the routes |
| Change site colours, type, spacing | `app/src/app.css` | no framework. Fonts are tokens, `--font-body` and `--font-head` |
| Swap a font | `@fontsource-variable/*` import in `app/src/routes/+layout.svelte`, then the token | not a CDN link; the site fetches nothing external |
| Stop building the site on a run | `config.json → web.build_on_run` | |
| Debug an empty or stale site | `cd app && npm run check` — asserts the sidecar contract and names broken digests | |
| Add a hard rule for the agent | `docs/RULES.md` | |
| Change lookback, item cap, fetch budget, candidate cap | `config.json → run` | |
| Change topic / geography focus / mute terms | `config.json → focus` | |
| Change output paths | `config.json → paths` | |
| Add Slack or another push target | `scripts/notify.py`: branch on `a.platform`, read `delivery.<name>` | `chat.sh` needs nothing |
| Change Telegram chunking | `config.json → delivery.telegram`; logic is `notify.py::chunks()` | |
| Test a source kind without hitting its API | `tests/test_fred.py` is the pattern: stub `<kind>.get`, assert the reading shape, per-series isolation, and that no secret reaches `errors[]` | |
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
| `tests/` | `unittest`, stdlib only. `test_fred.py` stubs the network; the live case runs only with a key present |
| `state/seen.json` | `{"ids":[…]}` published URL hashes. Agent appends |
| `state/candidates.json` | per-run payload: `candidates[]`, `tape{}`, `errors[]` |
| `digests/` | outputs, one `.md` and one `.json` per run. Gitignored |
| `vaults/` | Obsidian copy, markdown only. Gitignored |
| `app/` | SvelteKit reader, `adapter-static`. Prerendered, read-only, optional |
| `app/scripts/collect.mjs` | digests/*.json → `src/lib/data/{digests,index,rows,topics,tape,meta}.json`. `--check` asserts the contract |
| `app/src/routes/` | `/` today · `/archive` · `/d/[date]` · `/topics` + `/topics/[slug]` · `/tape`. Search has no route: the finder is in the masthead everywhere |
| `app/src/lib/` | `Digest`, `Entry`, `Tape`, `Finder`, `Filters`, `Results`, `Score`, `Icon`, `ThemeToggle`, `md.js`, `finder.svelte.js`. `data/` is generated, gitignored |
| `app/scripts/md.check.mjs` | asserts for the renderer, including against the real 2026-09-08 run notes |
| `PRODUCT.md` | who reads this, which jobs, what must not be renamed. Product truth, no visual decisions |
| `DESIGN.md` | the visual world: palette, type, structure, the rules the interface holds to |
| `app/static/` | files served at the site root, as-is. `favicon.jpg` today |
| `app/build/` | static output. Gitignored |

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

### Site copy

Text on the site is written the way a digest is. The reader is one person who
already knows what this repo does and does not need to be sold it.

- State the fact and stop. No "importantly", "it's worth noting", "this matters".
- No aside telling the reader what to notice. A sparkline showing one dot needs
  the caption "seen once" and nothing after it.
- Numbers and dates instead of adjectives. "13 entries from 2 digests", not
  "entries indexed across every digest". Not "strong", when the label can say `45+`.
- `·` separates, the way the tape lines do. Em dashes are not a rhythm device.
- A colon introduces a list, a label, or a value. Never a reveal.
- Say what failed, in the words of what failed: "2026-09-05 declared no topics".

Same test the digests use: a line that could sit unchanged on some other
product's page is filler. Cut it or replace it with a number.

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
| Tests beyond `--demo`, `npm run check` and `tests/` | those cover the parsers, interleave, registry resolution, the sidecar contract, and the fred kind | logic outgrows them |
| Auth on the site | it is localhost, or behind Cloudflare Access | it is served anywhere a stranger can reach |
| Editing or annotating a digest from the site | the agent owns digests; a second writer means two sources of truth | never, unless the annotation lives outside `digests/` |
| Tape charts with real numbers | `tape.readings` is null on the backfilled digests, so there is nothing to plot | a digest carries `readings`. The `Sparkline` component is already there |
| A full markdown parser | `md.js` covers what the digest shape allows: links, bold, inline code, lists, tables, headings | `docs/WORKFLOWS.md` widens what a digest may contain |
| Python deps, venv, uv | system 3.9 + stdlib suffices | stdlib stops being enough |

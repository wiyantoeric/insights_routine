# WORKFLOWS.md — the daily run

Triggered by cron. One workflow today; add others as separate sections.

## W1 — daily-scan

**Cadence:** daily, 07:00 Asia/Jakarta. **Budget:** ~12 web fetches, one agent session.

### 1. Ingest (deterministic, `scripts/fetch.py`)

- Read `config.json`, then every enabled spec in `sources/`.
- `content` sources (sitemap kind): fetch index, keep shards matching
  `child_match`, parse `<loc>` + `<lastmod>`, keep `lastmod >= now -
  run.lookback_days` on an `include_path` and not an `exclude_path`, drop ids
  already in `state/seen.json`, cap at the spec's `max_urls`.
- `tape` sources: CoinGecko crypto, Yahoo quotes with 1d change and z-score
  over the window, `alert: true` beyond the spec's `alert_sigma`. FRED when enabled.
- Interleave candidates round-robin by source, cap at
  `run.max_candidates_to_agent`.
- Write `state/candidates.json`.

Failure of one source must not abort the run. Record the error into the payload
under `errors` and continue.

### 2. Triage (agent, no fetches)

Read candidates. Drop `mute_terms` matches, off-theme titles, duplicate
coverage of one story. Cheap pass — titles and URL slugs only.

### 3. Deepen (agent, WebFetch)

For survivors, up to `run.max_agent_fetches` pages, sequential. Extract:
claim, hard numbers, any date or deadline, named sector, named geography.
Note whether a theme appears across more than one firm.

### 4. Score (agent)

Apply the `docs/OPPORTUNITIES.md` rubric. Discard below
`scoring.min_score_to_publish`. Keep top `run.max_items_per_digest`.

### 5. Write

- `digests/YYYY-MM-DD.md` — full digest.
- Copy to `paths.vault_dir/YYYY-MM/YYYY-MM-DD.md` with Obsidian frontmatter and
  `[[wikilinks]]` on recurring themes so the vault self-organizes over weeks.
- Append published URL hashes to `state/seen.json`.

### 6. Push

`scripts/notify.py` reads the digest, renders the short form, chunks at
`delivery.telegram.max_chars`, posts. Short form = headline, one-line why, score,
action, link. The vault holds the long form.

## Digest shape

```markdown
# Insights — 2026-09-05

**Tape:** BTC 111.2k (-1.4%) · IDX 7,412 (+0.3%) · USDIDR 16,280 (+0.1%) · US10Y 4.18% ▲2.1σ
> one line on what the tape contradicts or confirms in today's items

## 1. [Title] — score 47/60 · service_demand
**Signal:** what was published, with the number.
**Why it matters:** the mechanism that turns this into money or risk.
**Angle:** the specific offer, product, or position.
**Do this week:** one concrete action.
**Source:** url · published date

## Watchlist
- themes seen once, not yet strong enough. Carried forward.
```

## Adding a workflow

New section here, new prompt in `prompts/`, new block in `config.json`, new cron
line. Do not fork `run.sh`.

# WORKFLOWS.md: the daily run

Triggered by cron. One workflow today; add others as separate sections.

## W1: daily-scan

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

Read candidates. Drop `mute_terms` matches, off-topic titles, duplicate
coverage of one story. Cheap pass, titles and URL slugs only.

### 3. Deepen (agent, source-page fetch)

For survivors, up to `run.max_agent_fetches` pages, sequential. Extract:
claim, hard numbers, any date or deadline, named sector, named geography.
Note whether a topic appears across more than one firm.

### 4. Score (agent)

Apply the `docs/OPPORTUNITIES.md` rubric. Discard below
`scoring.min_score_to_publish`. Keep top `run.max_items_per_digest`.

### 5. Write

Write only the formats listed in `delivery.digest_archive.formats`. Both by
default. The vault copy and the Telegram push are markdown; the site is json.

- `digests/YYYY-MM-DD.md`: full digest. Format `markdown`.
- `digests/YYYY-MM-DD.json`: the same digest as data. Format `json`. Shape below.
- Copy to `paths.vault_dir/YYYY-MM/YYYY-MM-DD.md` with Obsidian frontmatter and
  `[[wikilinks]]` on recurring topics so the vault self-organizes over weeks.
  Markdown only; skipped when `markdown` is off.
- Append published URL hashes to `state/seen.json`. Always, whatever the formats.

### 6. Push

`scripts/notify.py` reads the digest, renders the short form, chunks at
`delivery.telegram.max_chars`, posts. Short form = headline, one-line why, score,
action, link. The vault holds the long form.

### 7. Publish (optional, `npm run build` in `web.dir`)

`app/scripts/collect.mjs` reads every `digests/*.json`, emits the site's data
layer, and SvelteKit prerenders one static page per digest, topic and view.
Runs only when `web.build_on_run` is true and npm is on PATH. A build failure is
a warning, never a failed run; the push already happened.

## Digest shape

```markdown
# Insights 2026-09-05

**Tape:** BTC 111.2k (-1.4%) · IDX 7,412 (+0.3%) · USDIDR 16,280 (+0.1%) · US10Y 4.18% ▲2.1σ
> one line on what the tape contradicts or confirms in today's items

## 1. [Title] · score 47/60 · service_demand
**Signal:** what was published, with the number.
**Why it matters:** the mechanism that turns this into money or risk.
**Angle:** the specific offer, product, or position.
**Do this week:** one concrete action.
**Source:** url · published date

## Watchlist
- topics seen once, not yet strong enough. Carried forward.
```

## Sidecar JSON

What `app/` reads, so nothing downstream parses prose. Written when
`delivery.digest_archive.formats` contains `json`. Same numbers as the markdown,
copied from it, never re-derived.

```json
{
  "date": "2026-09-08",
  "top_score": 37,
  "topics": ["pilot-to-production-gap", "geography-lag"],
  "tape": {
    "as_of": "2026-09-08T14:05Z",
    "as_of_note": "As-of 2026-09-08T14:05Z (IDX 09:00Z). No alerts, largest move is DXY at -0.89σ",
    "line": { "BTC": "77,907 (-1.9%)", "IDX": "6,686 (+1.0%)" },
    "line_remark": "anything in the tape line that is not an asset reading",
    "readings": {},
    "alerts": []
  },
  "tape_note": "the one-line read that sits under the tape",
  "items": [{
    "ord": 1,
    "title": "…",
    "score": 47,
    "lens": "product_idea",
    "signal": "…",
    "why": "…",
    "angle": "…",
    "action": "…",
    "sources": [{"url": "…", "published": "…"}],
    "follow_up": false
  }],
  "watchlist": [{"title": "…", "score": 26, "body": "…", "sources": []}],
  "run_notes": "…",
  "errors_present": false
}
```

- `sources` is a list. Items routinely carry more than one URL; a single-URL
  field drops claims.
- `sources[].url` is an absolute `http://` or `https://` url and nothing else.
  A repo path, a filename, or a sentence describing where you looked is not a
  url. Those belong in the prose or in `run_notes`. The reader shows a non-url
  source in the alert colour and refuses to link it.
- `tape.readings` is the `tape` block from `state/candidates.json`, copied
  verbatim. `null` when the digest was written without it to hand.
- `items` is empty on a zero-item day. `watchlist` and `run_notes` still carry.
- `lens` is one of `focus.lenses`. `score` is the composite out of 60.
- `tape.line` is one entry per asset: the key is the label, the value is the
  reading with its change in parentheses. One asset, one pair. The reader sets
  the label and the value as two things and tints the sign, which a single
  sentence of numbers cannot do.
- `tape.line_remark` takes whatever is in the tape line but is not an asset
  reading: the as-of stamps, "no move beyond 2.0σ", which close a price is from.
- `tape.as_of` is the bare timestamp; `as_of_note` is the whole as-of line
  verbatim, since it often carries the alert read too.
- `watchlist[].score` is `null` when the entry was never scored. Do not
  back-fill a number that was not written.
- `watchlist[].body` is the entry without its own title or score; both are
  separate fields and the reader renders them itself.
- `_backfilled`, when present, means the sidecar was reconstructed from the
  markdown rather than written by the agent. Provenance, not decoration.

## Writing the long fields

`signal`, `why`, `angle`, `action` and every `watchlist[].body` are read on a
screen, at length, in the morning. They are markdown and the reader renders
them. Write them to be read, not to be parsed back out of one block.

- **Paragraphs.** Separate them with a blank line. Two to four sentences each.
  Nothing over about 120 words without a break.
- **Lists.** Enumerations become `- ` bullets, one claim per bullet. A bullet
  that wraps continues on a line indented two spaces.
- **Tables.** Three or more values being compared go in a `|` table with its
  `|---|` divider row. Show the working: candidate, what was claimed, what is
  actually true.
- **References.** `[^1]` points at the first entry in that item's `sources`
  list, `[^2]` the second. The reader renders the marker as a superscript that
  jumps to the numbered source. Use an inline `[text](url)` only when the link
  text is the thing being named, not to carry a citation.
- **Code.** Backticks for file names, config keys and field names:
  `run.lookback_days`, `state/seen.json`, `child_match`.
- **No em dashes.** A comma, a colon, a semicolon or a new sentence does the
  work. This is a hard rule, see `docs/RULES.md`.

## Adding a workflow

New section here, new prompt in `prompts/`, new block in `config.json`, new cron
line. Do not fork `run.sh`.

# AGENTS.md — contract for any agent running in this repo

## What this repo is

A recurring intelligence routine. Every day it pulls what KPMG / Deloitte / PwC
published, pairs it with live market prices, scores each item for
**opportunity**, and pushes the top 3-5 to Telegram plus an Obsidian vault.

It is not a news summarizer. A digest that only tells the operator what happened
has failed. Each item must say **what to do about it**.

## Routing — which doc answers which question

All docs live in `docs/`. Each owns one function. Read the one that matches the
question; do not read them all by default.

| Question | Read | Function |
|---|---|---|
| What must I never do? | `docs/RULES.md` | Hard constraints. Truth, scope, output discipline, safety. A violation fails the run |
| What do I do, step by step, and what does the output look like? | `docs/WORKFLOWS.md` | The pipeline. W1 daily-scan, six steps, the required digest shape |
| What counts as an opportunity and how do I score it? | `docs/OPPORTUNITIES.md` | The scoring brain. Four lenses, rubric /60, hard zeros, anti-patterns |
| Where does content come from, and what is known to break? | `docs/SOURCES.md` | Source registry. Verified sitemap URLs, market endpoints, quirks, failure log |
| I want to change X — which file owns it? Do we already have Y? | `docs/ARCHITECTURE.md` | Task → file routing table, inventory of files, functions and handled behaviours, list of things deliberately not built |
| How does a human set this up and run it? | `README.md` | Getting started, cron, troubleshooting |

Not in `docs/`:

| File | Function |
|---|---|
| `config.json` | Run behaviour: `run`, `paths`, `focus`, `scoring`, `delivery`, `agent`. Sources are not here. Never written by the agent |
| `prompts/daily_scan.md` | The prompt the routine executes. Points at the docs above; does not repeat them |
| `sources/` | One file per source. `<id>.json` spec; `<kind>.py` when a kind needs code. Contract in `docs/SOURCES.md` |
| `core/` | Shared library: `http`, `sitemap`, `items`, `config`, `registry`. Reuse before writing |
| `scripts/` | `run.sh` orchestrates, `fetch.py` runs every source, `notify.py` delivers, `chat.sh` tests delivery |
| `state/` | `seen.json` dedup ledger, `candidates.json` per-run input, `run.log` |
| `digests/` | One markdown file per run |

## Read order for a daily run

1. `config.json`
2. `docs/RULES.md`
3. `docs/OPPORTUNITIES.md`
4. `docs/WORKFLOWS.md` § W1
5. `state/candidates.json`

`docs/SOURCES.md` only if `candidates.json → errors` is non-empty.
`docs/ARCHITECTURE.md` only when changing the repo, never during a run.

## Roles

One agent, three passes inside a single run. Do not spawn subagents — the
candidate list is small and the cost is not worth it.

1. **Triage** — read `state/candidates.json`. Kill anything matching
   `focus.mute_terms` or obviously off-theme. Cheap, no fetches.
2. **Deepen** — for surviving candidates only, WebFetch up to
   `run.max_agent_fetches` pages. Extract claims, numbers, dates.
3. **Score & write** — apply the `docs/OPPORTUNITIES.md` rubric, keep the top
   `run.max_items_per_digest`, write the digest.

## Run

```bash
./scripts/run.sh            # full daily run
./scripts/run.sh --dry      # fetch + score, no Telegram push
python3 scripts/fetch.py    # ingestion only, inspect state/candidates.json
```

Watching a run. `run.sh` streams one line per agent tool call, so a manual run
shows progress in the terminal and a cron run is followed with
`tail -f state/run.log`. `pgrep -fl "claude -p"` says whether the agent is
still alive. The stream prints the session id first; `claude -r <id>` reopens
that finished run interactively to ask it why it scored something the way it did.

## Invariants

- `config.json` is read, never written, by the agent.
- Every claim in a digest carries its source URL. No URL, no claim.
- Numbers are copied, never estimated. See `docs/RULES.md`.
- Config before prompt, prompt before code. If `config.json` can express a
  change, that is the only file touched.

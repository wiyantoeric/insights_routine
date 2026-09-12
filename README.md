# insights_routine

Daily opportunity scanner. Pulls what KPMG, Deloitte and PwC published in the
last few days, pairs it with live market prices, scores every item against a
written rubric, and pushes the top 3-5 to Telegram and an Obsidian vault.

Runs locally as a Claude Code headless session on a cron schedule. The routine
needs nothing beyond system Python, `jq`, and the `claude` CLI. The optional
web reader in `app/` is the only thing that wants Node, and only to build.

## Prerequisites

- macOS with `python3` (system 3.9 is fine) and `jq` (`/usr/bin/jq` ships with macOS)
- [Claude Code](https://claude.com/claude-code) CLI on `PATH`, logged in
- A Telegram bot token and your chat id ([@BotFather](https://t.me/BotFather) for the token, [@userinfobot](https://t.me/userinfobot) for the id)
- Optional: an Obsidian vault folder
- Optional: Node 20+ if you want the web reader (`app/`). The routine itself never needs it

## Setup

```bash
git clone <this repo> && cd insights_routine
cp .env.example .env          # fill TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
```

Open `config.json` and check two paths:

- `paths.vault_dir` — where digests are copied for Obsidian. Point it at your vault, or any folder you will open in Obsidian.
- everything else can stay as is for a first run.

Verify delivery before anything else:

```bash
scripts/chat.sh --platform telegram "hi there"
```

## First run

```bash
./scripts/run.sh --dry
```

Fetches candidates, runs the agent, writes the digest, skips the Telegram push.
Progress streams to the terminal one line per agent action. Expect 3-6
minutes and roughly 12 web fetches.

Outputs:

| What | Where |
|---|---|
| Digest | `digests/YYYY-MM-DD.md` |
| The same digest as data | `digests/YYYY-MM-DD.json` — what the web reader reads |
| Vault copy with frontmatter and wikilinks | `<paths.vault_dir>/YYYY-MM/YYYY-MM-DD.md` |
| Dedup ledger | `state/seen.json` |
| Raw input the agent saw | `state/candidates.json` |
| Static site, when `web.build_on_run` is on | `app/build/` |

### Read it in a browser

```bash
cd app && npm install     # first time only
npm run dev               # http://127.0.0.1:5173
```

`npm run build` writes a static site to `app/build` — plain files, no server,
serve them with anything, including `python3 -m http.server`. `npm run check`
asserts the digest sidecars are well-formed and names any that are not.

The home page is today's digest. Press `/` or `⌘K` anywhere to search every item
and watchlist entry ever published, filtered by firm, lens, score band or topic;
`Esc` clears it. `/archive` is the date index, `/topics` counts what recurs.

Three colour themes, light, beige and dark, from the swatches at the right of the
masthead. The choice is remembered in that browser; without one, the site
follows the system setting.

The site is a read-only projection of `digests/*.json`. Delete `app/` and the
routine is unaffected; delete the site's data and `npm run build` rebuilds it.

Send that digest to Telegram by hand to see how it reads on a phone:

```bash
scripts/chat.sh --platform telegram --file digests/$(date +%F).md
```

## Deploy on a VPS

Any Linux box with `python3` ≥ 3.9, `jq`, and Node for the `claude` CLI. The
same Node builds the web reader, which is why `web.build_on_run` defaults on.

```bash
sudo apt install -y jq python3 git
curl -fsSL https://claude.ai/install.sh | sh          # claude CLI, lands in ~/.local/bin
git clone <this repo> ~/insights_routine && cd ~/insights_routine
cp .env.example .env                                   # ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
scripts/chat.sh --platform telegram "vps up"           # delivery works?
./scripts/run.sh --dry                                 # full pipeline once, no push
```

`run.sh` sources `.env`, so `claude` finds `ANTHROPIC_API_KEY` without an
interactive login, and exports `~/.local/bin` onto PATH for cron.

Crontab (`crontab -e`). Server clocks are usually UTC; 07:00 Jakarta is 00:00 UTC:

```cron
MAILTO=""
# 07:00 Asia/Jakarta. Lock prevents overlap, timeout kills a hung agent run.
0 0 * * * cd $HOME/insights_routine && flock -n state/run.lock timeout 45m ./scripts/run.sh >> state/run.log 2>&1
```

If the server's timezone is set to Asia/Jakarta, use `0 7` instead. Check with `date`.

Follow a run with `tail -f state/run.log`. Each run prints its session id
first; `claude -r <session-id>` reopens it to ask why it scored something the
way it did. Keep `state/run.log` in check with a weekly
`find state -name run.log -size +5M -exec truncate -s 0 {} \;` cron line, or logrotate.

The vault is written to `vaults/` inside the repo. On a server nobody opens
Obsidian, so either sync that folder to where you read it (Syncthing, `rsync`,
a git remote), or point `paths.vault_dir` at a mounted share.

## Useful commands

```bash
python3 scripts/fetch.py                       # ingestion only, inspect state/candidates.json
python3 scripts/fetch.py --demo                # parser + source registry self-check
(cd app && npm run check)                      # sidecar contract + markdown renderer self-checks
python3 -m unittest discover -s tests          # source-kind tests; the fred live case needs a key
python3 scripts/notify.py                      # push newest digest
scripts/chat.sh --platform telegram "text"     # push arbitrary text
scripts/chat.sh --platform telegram --file f   # push any markdown file
```

To force a full re-scan, empty the `ids` list in `state/seen.json`.

## Tuning

Every knob is in `config.json`. The ones you will actually touch:

| Key | Does |
|---|---|
| `run.lookback_days` | How far back "new" reaches. 3 is a good default for daily |
| `run.max_items_per_digest` | Cap on published items. Fewer is fine; padding is the failure mode |
| `run.max_agent_fetches` | Web fetch budget per run. Drives cost and runtime |
| `focus.topics`, `focus.geo_boost` | What scores well. Geo is a boost, not a filter |
| `focus.mute_terms` | Hard drops in triage |
| `scoring.min_score_to_publish` | The bar, out of 60 |
| `delivery.digest_archive.formats` | Which digest files get written. `markdown` feeds Telegram and the vault, `json` feeds the site |
| `web.build_on_run` | Rebuild the static site at the end of each run. Needs npm on the box |

Sources are not in `config.json`. Each is one file in `sources/`: a JSON spec,
plus a small Python module when the kind needs code. Add a ticker in
`sources/quotes.json`, a firm as a new `sources/<id>.json`. Contract and
examples in `docs/SOURCES.md`.

Change the definition of "opportunity" in `docs/OPPORTUNITIES.md`. Change how the
agent works in `prompts/daily_scan.md`. Never hardcode in scripts what the
config can express.

## How it works

`run.sh` does four things in order:

1. `fetch.py` runs every enabled source in `sources/`. Sitemap sources are
   filtered by `lastmod` and path and deduped against `seen.json`; price
   sources return the day's tape. Results are interleaved by source, capped,
   and written to `state/candidates.json`. Deterministic, no LLM, ~15 seconds.
2. `claude -p` runs `prompts/daily_scan.md`. The agent reads the harness files,
   triages by title, fetches survivors, scores against the rubric, writes the
   digest and vault copy, updates `seen.json`.
3. `notify.py` chunks the digest and posts it to Telegram.
4. `npm run build` in `app/` prerenders the reader from the json sidecars, when
   `web.build_on_run` is on. Last, and never fatal — the push is the job.

The harness files the agent reads, in order: `AGENTS.md` (contract and file
map), `docs/RULES.md` (hard constraints), `docs/OPPORTUNITIES.md` (signal taxonomy and
scoring), `docs/WORKFLOWS.md` (pipeline and digest shape), `docs/SOURCES.md` (source
registry and failure log). Start with `docs/ARCHITECTURE.md` if you want to change
anything: it maps each kind of change to the one file that owns it.

## Troubleshooting

**macOS "Malicious Script Blocked" dialog.** XProtect on macOS 26 kills shell
scripts that hide their output while a child process bursts network traffic.
`run.sh` is written to avoid that shape. Do not wrap it in `exec > >(tee …)`
or similar. Details in the `docs/SOURCES.md` failure log.

**Zero candidates two runs running.** A sitemap moved. Check `docs/SOURCES.md` for
the verified URLs and re-probe `robots.txt` on the firm's domain.

**Telegram push fails with a Markdown parse error.** `notify.py` retries the
chunk as plain text automatically. If it still fails, the token or chat id is
wrong; `scripts/chat.sh "hi"` isolates that.

**Agent run costs too much.** Lower `run.max_agent_fetches` and
`run.max_candidates_to_agent` in config. Yesterday's run was ~30 turns.

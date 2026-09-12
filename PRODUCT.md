# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

One operator based in Jakarta, working alone. Reads in the morning after the
07:00 Asia/Jakarta cron run has already pushed the short form to Telegram. Uses
a Mac at a desk and a phone, and does the same work on both — the phone is not a
skim surface.

Two jobs dominate, in equal measure:

1. **Read today and decide.** Work through today's items and their "do this
   week" actions.
2. **Find one specific past item.** A remembered claim, number, firm or topic
   from an earlier digest.

A third job, looking for patterns across weeks (recurring topics, vocabulary
migration, what the watchlist keeps carrying), matters but ranks below those two.

## Product Purpose

`insights_routine` reads what KPMG, Deloitte and PwC publish as a demand signal
rather than as news. Each day it scores candidate items against a written rubric
out of 60 and publishes only those clearing 40. Every published item ends in one
concrete action doable that week. Zero items is a valid, correct day.

This web reader is the surface where the operator works through those items and
retrieves past ones. It is a read-only projection of `digests/*.json`; the agent
writes, the reader never does.

## Positioning

Consulting insight pages are marketing. Read straight they are noise; read as
publication *behaviour* they are a free demand-sensing network paid for by three
firms with thousands of client conversations behind every publication. The
routine's four lenses (service demand, product ideas, market intel, meta
signals) and its narrative-vs-tape comparison are what a news summarizer cannot
copy.

## Operating Context

- Cron runs at 07:00 Asia/Jakarta. Telegram carries the short form; the vault
  carries an Obsidian copy; this reader carries the full archive.
- Search today happens in third-party apps (the Obsidian vault, Telegram
  scrollback). The reader owning search is the main reason for this redesign.
- Deployed from a VPS as static files, or read on localhost. Digests name real
  prospects and pricing angles, so it stays behind localhost or Cloudflare
  Access.

## Capabilities and Constraints

- Content unit: an **item** — title, score out of 60, lens, signal, why it
  matters, angle, do-this-week action, one or more sources with published dates.
- Second unit: a **watchlist entry** — title, optional score, body, sources.
  Carried forward across days.
- A digest also carries: the tape (a written market line, an as-of stamp, alert
  flags, optionally numeric readings), a one-line tape read, declared topics,
  and run notes recording ingestion failures.
- Vocabulary that must not be renamed: Signal, Why it matters, Angle, Do this
  week, Watchlist, Run notes, Tape, lens, score, follow-up.
- Lenses come from `config.json`: `service_demand`, `product_idea`,
  `market_intel`. The publish bar (40) and max score (60) come from the same
  file and must never be hardcoded in the UI.
- Static output only. No server, no database, no runtime fetch. Every page is
  prerendered by SvelteKit with `adapter-static`.
- Data can be sparse or absent: a digest may declare no topics, carry no numeric
  tape readings, or publish zero items. The UI must show what is missing rather
  than infer or smooth it.

## Brand Commitments

- Fonts are fixed: **Noto Sans** for body, **Urbanist** for headings, both
  self-hosted. No external font request.
- Visual direction: minimalist, but distinct from an ordinary website. Creative
  interface elements are welcome at low priority — never at the cost of the two
  dominant jobs.
- Copy follows `docs/ARCHITECTURE.md § Site copy`: state the fact and stop, no
  asides telling the reader what to notice, numbers instead of adjectives.

## Evidence on Hand

- Two real digests, `digests/2026-09-05.json` (4 items, 6 watchlist entries) and
  `digests/2026-09-08.json` (zero items, 3 watchlist entries, long run notes),
  both reconstructed from their markdown and flagged `_backfilled`.
- No numeric tape readings exist yet on either digest — the tape is a written
  line only. Charts must not be faked from it.
- 2026-09-05 declared no topics. Nothing may be inferred for it.

## Product Principles

1. **The item is the atom.** A digest is a container; an item with a score, a
   lens and an action is the thing being read and retrieved.
2. **Retrieval is a first-class job, not a page.** Finding one past item must
   never require navigating somewhere first.
3. **Show what is missing.** Absent topics, absent readings, broken digests and
   zero-item days are reported plainly. Silent degradation is how this rots.
4. **Numbers are copied, never estimated.** The same rule the digests follow
   applies to anything the interface derives or draws.
5. **The reader is optional.** Delete it and the routine is unaffected.

## Accessibility & Inclusion

No product-specific standard established. Phone and desktop are equal targets,
so every view must work at ~390px, and the interface must be operable from the
keyboard.

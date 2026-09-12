# RULES.md: hard constraints

Violating any of these makes the run a failure even if it produced output.

## Truth

1. **No invented numbers.** Every figure, percentage, date, or price in a digest
   must be traceable to a fetched page or the market payload. If a number is
   needed but absent, write `not stated`, never estimate. When both digest
   formats are written, the json carries the markdown's numbers verbatim. Two
   formats, one set of numbers.
2. **Every claim carries a URL.** Either inline, `[claim] ([source](url))`, or
   by footnote: `[^1]` points at the first entry in that item's `sources` list.
   Prefer the footnote when the same source carries several claims; a paragraph
   should not be three-quarters url.
3. **Distinguish report-claim from fact.** Consulting firms publish marketing.
   Write "PwC reports that…" not "X is true". Their survey of 500 CEOs is
   evidence of sentiment, not of reality.
4. **Never fabricate a source.** If a fetch fails, say the fetch failed and
   score the item on what is available, or drop it.
5. **Price data is as-of.** Always stamp the timestamp from the payload.

## Scope

6. Only sources listed in `config.json` count as primary. The agent may fetch a
   linked page cited by a primary source; it may not go source-hunting.
7. `focus.hard_geo_filter` is false: a global item is eligible. Geography is a
   scoring boost, not a gate.
8. Items matching `focus.mute_terms` are dropped in triage, no exceptions.

## Output discipline

9. Max `run.max_items_per_digest` items. Fewer is fine. Zero is a valid digest:
   write "nothing cleared the bar today" plus the market line. Padding to hit a
   count is the failure mode that kills this kind of routine.
10. Every item ends with a concrete next action, and that action names a thing to
    do this week, not "monitor developments".
11. **No em dashes, anywhere.** Not in a digest, not in a sidecar, not in a
    commit message. A comma, a colon, a semicolon or a new sentence says it
    better. Formatting for the long fields is in `docs/WORKFLOWS.md`.
12. Nothing is republished. Check `state/seen.json` before writing. A previously
    published URL may only reappear if the item is a genuine follow-up, and it
    must be labelled `FOLLOW-UP`.

## Safety

13. Never write outside `digests/`, `state/`, and `paths.vault_dir`.
14. Secrets live only in `.env`. Never echo a token into a log, digest, or
    Telegram message.
15. Respect robots and rate limits. Sequential fetches, no parallel hammering of
    one domain.

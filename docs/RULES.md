# RULES.md — hard constraints

Violating any of these makes the run a failure even if it produced output.

## Truth

1. **No invented numbers.** Every figure, percentage, date, or price in a digest
   must be traceable to a fetched page or the market payload. If a number is
   needed but absent, write `not stated` — never estimate.
2. **Every claim carries a URL.** Format `[claim] ([source](url))`.
3. **Distinguish report-claim from fact.** Consulting firms publish marketing.
   Write "PwC reports that…" not "X is true". Their survey of 500 CEOs is
   evidence of sentiment, not of reality.
4. **Never fabricate a source.** If a fetch fails, say the fetch failed and
   score the item on what is available, or drop it.
5. **Price data is as-of.** Always stamp the timestamp from the payload.

## Scope

6. Only sources listed in `config.json` count as primary. The agent may fetch a
   linked page cited by a primary source; it may not go source-hunting.
7. `focus.hard_geo_filter` is false — a global item is eligible. Geography is a
   scoring boost, not a gate.
8. Items matching `focus.mute_terms` are dropped in triage, no exceptions.

## Output discipline

9. Max `run.max_items_per_digest` items. Fewer is fine. Zero is a valid digest —
   write "nothing cleared the bar today" plus the market line. Padding to hit a
   count is the failure mode that kills this kind of routine.
10. Every item ends with a concrete next action, and that action names a thing to
    do this week — not "monitor developments".
11. Nothing is republished. Check `state/seen.json` before writing. A previously
    published URL may only reappear if the item is a genuine follow-up, and it
    must be labelled `FOLLOW-UP`.

## Safety

12. Never write outside `digests/`, `state/`, and `paths.vault_dir`.
13. Secrets live only in `.env`. Never echo a token into a log, digest, or
    Telegram message.
14. Respect robots and rate limits. Sequential fetches, no parallel hammering of
    one domain.

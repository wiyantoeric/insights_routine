# OPPORTUNITIES.md — what to actually look for

The scoring brain. Read fully before scoring anything.

Consulting insight pages are marketing. Read straight, they are noise. Read for
the signals below, they are a free demand-sensing network paid for by three
firms with thousands of client conversations behind every publication.

The core move: **do not read what they say, read what their saying it implies.**
A firm publishes on a topic because it is selling into that topic. Publication
volume is a leading indicator of where enterprise budget is being aimed.

---

## Lens A — service / consulting demand

What tells you a client will soon need to buy something.

| Signal | Where it shows up | Why it converts |
|---|---|---|
| **Compliance deadline with a date** | Regulatory explainers, "what X means for you" | A date forces budget release. Highest-conviction signal there is. Log the date; work backwards 6-9 months for the sales window |
| **Survey stat on planned spend** | "X% of executives plan to invest in Y in 12 months" | Sizes the demand and gives you the headline number to quote back in a pitch |
| **Skills-gap language** | "organizations lack the talent to…" | Direct opening for staffing, training, managed service |
| **Pilot-to-production gap** | "stuck in pilot", "failed to scale", "POC purgatory" | The single most reliable consulting entry point in AI work right now |
| **Same pain in ≥2 of 3 firms within 30 days** | Cross-firm | Validation. One firm alone may be pushing a practice area; two is a market |
| **Cost or ROI benchmark** | Anywhere a number per-seat / per-process appears | Prices your own offer against a number the client already believes |
| **New named framework or maturity model** | Thought-leadership pieces | Clients will ask to be assessed against it. Be the one who assesses |

Regulatory deadlines to track by name (highest value, check every item for them):
EU AI Act phase dates, DORA, CSRD/ISSB & IFRS S1-S2, Basel III endgame,
PSD3, MiCA, and Indonesian equivalents — OJK POJK circulars, Bank Indonesia
payment rules, UU PDP (personal data) enforcement, Komdigi AI guidance.

## Lens B — product / build ideas

| Signal | Read as |
|---|---|
| A workflow described as manual, fragmented, or slow | Automation target. The report has done your user research |
| A framework, checklist, or maturity model published as prose | Turn it into a self-assessment tool. Prose framework wants to be software |
| "No standard exists yet" / "tooling is immature" | Green field, short window |
| A benchmark the firm charges to run | Ask whether public data reproduces 80% of it |
| A diagram with 5+ boxes and no vendor named | Nobody owns that category yet |
| Data the report cites but does not publish | If the underlying source is public, the aggregation is the product |

Bias toward things buildable in weeks, sold to a segment the report already
named. The report supplies the market sizing you would otherwise pay for.

## Lens C — market / investment intel

| Signal | Read as |
|---|---|
| Sector capex commentary (raised vs cut) | Rotation, ahead of the print |
| M&A volume and valuation talk | Where consolidation is starting |
| Supply chain / input cost warnings | Margin pressure downstream, one or two quarters out |
| A topic called hot while the tape has not moved | The most valuable single pattern in this system — see below |
| A topic dropped after months of coverage | Hype ending. Fade it |

**Narrative-vs-tape divergence.** This is why market data is in this repo. Four cases:

- Narrative hot, price flat → possible early entry, or the narrative is a sell-side pitch. Check who benefits from the report.
- Narrative hot, price already run → late. Do not build a business on it.
- Narrative silent, price moving → something is happening the reports have not caught. Highest-value gap; go find the primary cause.
- Both flat → ignore.

Tape watched daily: BTC, ETH, SOL, S&P 500, Nasdaq, IDX Composite, USD/IDR,
US 10Y yield, dollar index, gold, WTI. Flag any move beyond
`alert_sigma` in `sources/quotes.json` and ask which of today's items it touches.

## Lens D — meta signals (cheap, chronically underused)

These need no fetching, only the candidate list. They are often the best item
in the digest.

- **Volume shift.** One firm goes from 1 to 5 pieces on a topic inside a month → they see budget. Track counts per topic per week.
- **Vocabulary migration.** "AI" → "generative AI" → "agentic AI" → "AI governance". Whichever term is climbing is where the next 12 months of spend goes. Whoever adopts the new term first sounds current in a pitch.
- **Sequencing across firms.** One firm publishes, the other two follow within three weeks → consensus, you are already late. Only one firm and no followers after a month → either an edge or a dud; the tape decides which.
- **Geography lag.** A topic mature in the US/UK feeds with no Indonesian or SEA equivalent → a 12-18 month arbitrage window. This is the single highest-value pattern for an Indonesia-based operator, and it costs nothing to spot.
- **Silence.** A firm that covered a topic monthly and then stops. Something changed.

## Scoring rubric

Score each dimension 0-5, multiply by the weight in `config.scoring.dimensions`,
sum. Max 60. Publish at ≥ `scoring.min_score_to_publish`.

| Dimension | ×w | 0 | 5 |
|---|---|---|---|
| **Actionability** | 3 | Interesting, nothing to do | A specific offer, build, or position is obvious from the item |
| **Urgency** | 2 | No time element | A dated deadline or a live price move inside 90 days |
| **Monetizability** | 2 | No path to revenue | Named buyer, named budget line, plausible price tag |
| **Geo relevance** | 1 | No tie to Indonesia/SEA | Directly about, or a clean lag-arbitrage into, the region |
| **Confidence** | 2 | Single vendor assertion | Multiple firms, or hard third-party data behind it |
| **Novelty** | 2 | Covered in a past digest | Not seen in this repo before, and not obvious |

Tie-break: prefer the item with a **date** in it.

Hard zeros — discard regardless of other scores: award announcements, hires,
office openings, event promos, pure product marketing, anything already in
`state/seen.json` and not a genuine follow-up.

## Anti-patterns

- Publishing 5 items because the config allows 5. Three good beats five padded.
- "Monitor developments" as an action. Not an action.
- Treating a survey of executives as a fact about the world.
- Rewriting the firm's abstract. If an item's *Signal* line could have been copied from the page, it added nothing.
- Chasing whatever is loudest. The loudest topic is the most crowded one.

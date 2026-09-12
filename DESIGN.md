# Design

<!-- impeccable:design-schema 1 -->

## The world

**A research desk's morning tearsheet, filed in a catalogue.**

The audience's world is not SaaS. It is the sell-side morning note, the
pre-market tape strip, the regulatory circular with its effective dates, and the
archive drawer you go to when you need the one card from three weeks ago. Two
traditions, because two jobs:

- **The tearsheet** serves reading today. A masthead with the date and the tape
  ribbon. Numbered items separated by hairline rules. Score, lens and source in
  the gutter, the way a research note keeps its apparatus in the margin. The
  action set apart, because it is the payload.
- **The catalogue** serves retrieval. A finder that lives in the masthead on
  every page, filters as a row of small controls, and an occurrence strip that
  marks which days a topic appeared.

Anti-reference: the previous version of this site, a stack of same-size rounded
cards with a four-tab nav and search behind one of the tabs. Cards flattened
every content type into one shape, and hiding retrieval behind a tab is what
made the second job fail.

## Palette

Ink on paper, warm rather than blue-gray. One accent, used only where an action
or a live filter lives. Three colour themes, all of them the same desk:

- **Light.** The sheet as it comes off the printer.
- **Beige.** Aged manila. Warmer ground, browner ink, olive for the flag
  because a cool green goes sickly on it. Not light with a tint applied.
- **Dark.** The same desk under a lamp. Not an inversion: the ground keeps its
  warmth and the ink softens instead of going pure white.

| Token | Light | Beige | Dark | Use |
|---|---|---|---|---|
| `--paper` | `#faf8f4` | `#ece4d3` | `#16151a` | page ground |
| `--sheet` | `#ffffff` | `#f5efe2` | `#1d1c22` | raised surface: finder, sticky masthead |
| `--ink` | `#17161b` | `#2b2013` | `#eae7e0` | body |
| `--ink-2` | `#605c55` | `#6b5c45` | `#9b968d` | apparatus: dates, sources, labels |
| `--rule` | `#e0dcd3` | `#d3c7ac` | `#312f38` | hairlines |
| `--accent` | `#9a4f1b` | `#9a4f1b` | `#e0954f` | action, active filter, focus ring |
| `--flag` | `#1f6f4d` | `#4a6b32` | `#69c397` | cleared the bar, alert-free |
| `--alert` | `#a33a26` | `#a33a26` | `#e0765c` | tape alert, broken digest |

Every non-ink text colour is tinted from the ground's hue. No neutral gray.
Every pairing clears 4.5:1; the tightest is beige `--accent` on `--paper` at
4.7:1.

**How a colour theme is chosen.** `:root` carries the light tokens, so no colour is
defined only inside a media query. An explicit choice is stamped on
`<html data-theme>` and stored under `insights-theme`; an unstamped root follows
`prefers-color-scheme`. An inline script in `app.html` stamps the stored value
before first paint, so the page never flashes the wrong ground. The three
swatches in the masthead are literal theme colours, which is the one place
hard-coded hex belongs.

## Type

- **Urbanist Variable.** Masthead wordmark, headings, the uppercase apparatus
  labels. Tracking `-0.02em` on display sizes, `+0.09em` on uppercase labels.
- **Noto Sans Variable.** Body, controls, chips. 16px / 1.65, measure 68ch.
- **Numbers.** `font-variant-numeric: tabular-nums` everywhere a number can sit
  under another number: scores, tape, dates, counts. Non-negotiable; the tape
  ribbon is a column of figures whether or not it looks like one.
- Monospace appears only on the tape ribbon and on file or field names, which
  are literal data and code. Never as a costume for "technical". Inline code
  carries a faint accent tint, so a field name reads as marked rather than as a
  code block.
- Run notes render as real blocks: paragraphs, bullets, and a table with
  uppercase headers and hairline rules. The table scrolls rather than wrapping a
  date down a line.

## Structure

- **Masthead**, sticky, on every page: wordmark, the date of the newest digest,
  the finder, the section links, then the three colour swatches. It is the only
  persistent chrome.
- **The finder** is a single text field plus four filters (firm, lens, score
  band, topic). It opens with `/` or `⌘K` from anywhere, filters as you type,
  and results replace the page body in place. Its data chunk loads on first open,
  so no page pays for it until used.
- **Items** are separated by hairline rules, not boxed. On desktop a 9rem gutter
  carries the ordinal, score, lens and follow-up flag; the body runs in the
  measure beside it. Under 900px the gutter becomes a single line above the
  title.
- **The action** sits in its own block with the accent rule and a label. It is
  the one element allowed to interrupt the reading rhythm.
- **The occurrence strip** is one tick per digest in the archive, filled on days
  a topic was declared. It is an index, not a chart: at two digests it reads as
  two ticks and claims nothing.

## Prose

The site renders what the agent wrote, so the two ends agree on one format.
`docs/WORKFLOWS.md § Writing the long fields` is the writing end; this is what
the renderer guarantees.

- **Paragraphs** are blocks with air between them, never a wall. A blank line in
  the source is a paragraph break on the page. Body measure stays at 68ch.
- **Bullets** hang at 1.1rem with a wrapped line indenting under its own text,
  so the list reads as a list at a glance.
- **Tables** get uppercase headers, hairline rules, tabular figures, and
  horizontal scroll. A value never wraps mid-number.
- **References** are superscript numerals in the accent colour. `[^1]` in the
  source jumps to source 1 in that item's numbered list, and the target
  highlights when you land on it. This keeps prose readable: the claim carries a
  small numeral, not a 90-character url.
- **Inline code** is a tinted mark, for file names, config keys and field names.
- **No em dashes**, on the page or in this repo's own prose. A comma, a colon,
  a semicolon or a new sentence. The one exception is historical digest content,
  which is data and is never rewritten.
- **Tape readings** are label-and-value pairs, never a sentence of numbers. The
  delta keeps the sign the digest recorded and takes the only colour in the row.

## Motion

One authored moment: results in the finder settle in with a 140ms
exponential ease-out and a 2px rise, staggered 12ms per row and capped at
ten rows. Everything else is state, not animation. Respects
`prefers-reduced-motion`.

## Browser surfaces

Selection, caret, focus ring, scrollbar and underline offset are all themed from
the palette. Focus is a 2px accent ring with a 2px offset, visible on every
interactive element, never removed.

## Rules

- No cards. Rules and space do the separating.
- No icon fonts, no emoji, no unicode arrows standing in for icons. The three
  drawn glyphs (chevron, search, alert) are inline SVG on one 1.5px stroke.
- Nothing renders a trend from fewer than five points. Occurrence strips and
  counts only.
- Every derived number is traceable to the digest that carries it.

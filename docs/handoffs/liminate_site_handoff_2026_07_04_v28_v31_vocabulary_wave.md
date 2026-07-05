# Liminate Site Update — Handoff Packet

**Date:** 2026-07-04
**Source:** Liminate checkpoints v28 (Unless on Deontics Design Lock), v29 (Calendar Era Design Lock), v30 (Calendar Era Build Completion), v31 (Definitional Era Design Lock) — all July 4, 2026. Verified against `src/liminate/vocabulary.py` on `liminate@main`.
**Scope:** Vocabulary expanded from **60 → 61 reserved words** (21 verbs, 22 connectives, 10 operators, 3 articles, 3 multi-word reserved, 2 declarations). One new word: `define` (a declaration, joining `about`). Two grammar/value-type extensions that added **zero** new words: `unless` exception clauses on the deontic verb family (`require`/`forbid`/`permit`/`expect`), and the Calendar Era's `date` as a third scalar value type. Version v0.15.0 → v0.16.0. Test count 1499 → 1654.

**Status of this packet:** Unlike prior handoff packets in this directory, the `liminate-dev` changes described below were **already executed directly** this session (Claude Code has write access to the `liminate-dev` repo locally) rather than left as a pending handoff. This packet is the record of what changed, not an instruction queue. Branch: `docs/propagate-v28-v31-vocabulary-wave` in `liminate-dev`, not yet pushed or merged.

## Pages Updated

| Page | Path | What changed |
|---|---|---|
| Ecosystem README | `README.md` | "58 reserved words" → "61 reserved words" |
| Receipts app shell | `static/index.html` | Syntax-highlighter JS: `VERBS` set `combine`→`sum`, `OPERATORS` set +`highest`/`lowest`, `DECLARATIONS` set +`define`. This was a **functional** fix, not just copy — those tokens weren't highlighting correctly before. |
| Landing page | `static/landing.html` | Hero stat `58`→`61`; "58-word interpreter" headline; "58-word vocabulary" in the how-it-works copy |
| Mood Ring reading page | `static/moodring-reading.html` | "58-word" → "61-word"; "58 reserved words" → "61 reserved words" |
| Mood Ring product page | `static/moodring.html` | OG/Twitter meta description + footer copy, "58 words" → "61 words" |
| Pulse product page | `static/pulse/index.html` | OG meta description, "58 words" → "61 words" |
| Site home | `static/site/index.html` | Status pills: `v0.14.0`→`v0.16.0`, `1456 tests`→`1654 tests`, `58 reserved words`→`61 reserved words` |
| Language reference doorway | `static/site/language/index.html` | Meta description + lede + vocabulary-page teaser + values-page teaser (added "dates"), all `58`→`61`, operator/declaration counts updated |
| Vocabulary reference | `static/site/language/vocabulary/index.html` | Full refresh: word count, verb table (`combine`→`sum`), operator table (+`highest`/`lowest`), declaration table (+`define`), and **new prose** (both plain-English and technical registers) covering `unless`-on-deontics, the Calendar Era, and the Definitional Era |
| Values reference | `static/site/language/values/index.html` | Added `date` as a value type, with a short explanation and example |
| Spec/repo page | `static/site/spec/index.html` | Rewrote the dated `v0.14.0` status snapshot in place to `v0.16.0` / 61 words / 1654 tests, appending the v0.15.0 wave and v0.16.0 features to the technical-register feature list |

## Content Diffs

### `static/site/language/vocabulary/index.html`

**Current text (plain-English lede):** "Fifty-eight reserved words." / "The only other words allowed are the names you make up yourself and the values you write — like numbers and text."
**Updated text:** "Sixty-one reserved words." / "...like numbers, dates, and text."

**New paragraphs added** (both plain and technical registers) covering:
- `unless` exception clauses on `require`/`forbid`/`permit`/`expect` — framed as "no new word, it just learned a new place to stand"
- The Calendar Era's `date` value type — framed as "recognized by its shape, the way a number already was"
- The Definitional Era's `define` declaration — framed as "the newest word... names a rule so you can reuse it"

### `static/site/spec/index.html`

**Current text:** `Status: v0.14.0. Current source has 58 reserved words, 139+ locked test sentences, and 1456 pytest cases.`
**Updated text:** `Status: v0.16.0. Current source has 61 reserved words, 139+ locked test sentences, and 1654 pytest cases.` — plus the technical-register feature list extended with the v0.15.0 vocabulary wave and v0.16.0's three additions.

## New Pages (if any)

None. No new page is warranted — `unless`-on-deontics and the Calendar Era are grammar/value-type extensions of existing pages (vocabulary, values), not new surfaces.

## Style and Tone Notes

The site's language pages run a dual-register pattern throughout (`data-plain` / `data-tech` spans toggled by a reading-mode switch). Plain-English register stays concrete and avoids implementation jargon ("it just learned a new place to stand" rather than "new grammatical position"); technical register uses precise interpreter vocabulary (AST node names, parse-time vs. runtime, etc.). New copy added this pass follows both registers consistently with the surrounding page. No marketing language or hype was introduced — all claims trace to the checkpoints and to `vocabulary.py`.

## Do Not Change

- `static/moodring-archive.html`, `static/case-study-*.html`, `static/legal-*.html` — out of scope, no vocabulary references found
- `static/agreements*.html`, `static/sentinels*.html`, `static/translate*.html` — separate product surfaces, not scanned this pass (no evidence they reference the reserved-word count)
- Anything under `benchmarks/` — historical performance records
- Prior handoff packets in this directory — archival, never modified

## Not In Scope This Pass

Per the architect's explicit call: `liminate-receipts` was not scanned or updated — it is superseded by `liminate-dev` (Receipts now lives at `liminate.dev/receipts`, served by this repo) and is not a separate propagation target going forward.

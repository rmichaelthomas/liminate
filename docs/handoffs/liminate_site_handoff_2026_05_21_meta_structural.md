# Liminate Site Update — Handoff Packet

**Date:** 2026-05-21
**Source:** Meta-Structural Era build sessions — PR #15 (`about`), PR #16 (`because`), PR #17 (`inherited`), all merged to `liminate@main`. Source of truth: `src/liminate/vocabulary.py` (54 reserved words).
**Scope:** Vocabulary expanded from 51 → 54 reserved words across three batches whose site passes had been deferred. Net: +1 declaration (`about`), +1 connective (`because`, 19 → 20), +1 single-word operator (`inherited`, 7 → 8). Version v0.4.0 → v0.7.0; tests 1053 → 1160.

> **Note:** The site changes below have already been applied directly on branch `docs/propagate-meta-structural-era` in `liminate-site` (Claude Code CLI executes propagation directly). This packet records what changed for review/deploy; it is not a to-do list unless the branch is discarded.

## Pages Requiring Updates

| Page | Path | What to change |
|---|---|---|
| Homepage | `index.html` | Hero pill `51 reserved words` → `54`; tech variant `19 verbs, 19 connectives` → `20 connectives`; version pill `v0.4.0` → `v0.7.0` |
| Language index | `language/index.html` | Meta description, plain lede, tech lede (counts + add declaration category), and vocabulary nav blurb: `51` → `54`, `19 connectives` → `20`, `7 operators` → `8`, add `1 declaration` |
| Vocabulary | `language/vocabulary/index.html` | Title `Fifty-one` → `Fifty-four`; meta description; Connectives row `+because`; Operators row `+inherited`; new `Declarations` row (`about`); two new explanatory paragraphs (plain + tech) on the three inert self-describing words |
| Spec | `spec/index.html` | Interpreter status: `v0.4.0` → `v0.7.0`, `51 reserved words` → `54`, `1053 pytest cases` → `1160`; tech line notes Meta-Structural Era metadata |

## Content Diffs

### `language/vocabulary/index.html` (the substantive page)

**Connectives — current:** `… , over, then, by`
**Connectives — updated:** `… , over, then, by, because`

**Operators — current:** `is, above, below, not, plus, minus, reverse, plus equal/multiplied/divided …`
**Operators — updated:** `is, above, below, not, plus, minus, reverse, inherited, plus equal/multiplied/divided …`

**New row added:** `Declarations` → `about`

**New paragraphs (after the table):**
- *(plain)* "The newest three words describe the program itself rather than running: `about` names the topic, `because` records why a line exists, and `inherited` marks a line as carried over from a prior context. They show up when the program is read back, but never change what it does."
- *(tech)* "The Meta-Structural Era added three inert self-describing words — `about` (program topic declaration), `because` (statement-terminal quoted rationale), and `inherited` (statement-initial provenance modifier, with optional `from <agent>` attribution). All three are visible to rendering and `inspect` but never executed."

## New Pages (if any)

None. All changes are edits to existing pages.

## Style and Tone Notes

The liminate-site uses a paired `data-plain` / `data-tech` voice on most copy — plain-English framing for newcomers, precise terminology for the technical reader. Every count or list edited above appears in BOTH variants where the page uses the pattern; keep them in sync. The site avoids marketing language and version hype — state the count and the mechanism, nothing more. The three new words are **inert metadata** — the copy must not imply they affect execution.

## Do Not Change

- `language/pipeline/index.html` line ~43: "v0.2.0 dispatches pack verbs through parser, analyzer, and interpreter tables …" — a correct historical reference to when pack verbs landed, not a current-version claim. Left as-is.
- Any archival/philosophical framing that is correct regardless of vocabulary count.
- The "139 locked test sentences" figure on the spec page — a distinct metric not part of this vocabulary change; preserved unchanged (no current value available).

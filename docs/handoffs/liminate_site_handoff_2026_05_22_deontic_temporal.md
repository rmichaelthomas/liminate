# Liminate Site Update — Handoff Packet

**Date:** 2026-05-22
**Source:** Deontic Era + Temporal-Boundary Era build sessions — PR #32 (`forbid`), PR #33 (`permit`), PR #34 (`starting`/`until`), all merged to `liminate@main`. Source of truth: `src/liminate/vocabulary.py` (58 reserved words). Released as **v0.8.0** (confirmed live on PyPI).
**Scope:** Vocabulary expanded from **54 → 58 reserved words**: +2 verbs (`forbid`, `permit` — 19 → 21) and +2 connectives (`starting`, `until` — 20 → 22). Version v0.7.0 → v0.8.0. Test count 1160 → 1303 pytest cases.

## Pages Requiring Updates

| Page | Path | What to change |
|---|---|---|
| Homepage | `index.html` | Version pill `v0.7.0` → `v0.8.0`; vocabulary pill `54 reserved words` / `19 verbs, 20 connectives` → `58` / `21 verbs, 22 connectives`; "1053 automated checks" → `1303` |
| Spec | `spec/index.html` | Status line: `v0.7.0` → `v0.8.0`, `54 reserved words` → `58`, `1160 pytest cases` → `1303`; tech line — append Deontic + Temporal-Boundary eras to the era list |
| Language | `language/index.html` | Meta description + both lede modes: `54 reserved words` → `58`; tech breakdown `19 verbs, 20 connectives` → `21 verbs, 22 connectives` |
| Vocabulary | `language/vocabulary/index.html` | Page title `Fifty-four` → `Fifty-eight`; add `forbid`/`permit` to Verbs row, `starting`/`until` to Connectives row; add a paragraph on the Deontic + Temporal-Boundary words |

## Content Diffs

### `index.html`

**Line 35 — version pill**
Current: `<span class="pill"><span data-plain>v0.7.0</span><span data-tech>v0.7.0</span></span>`
Updated: `<span class="pill"><span data-plain>v0.8.0</span><span data-tech>v0.8.0</span></span>`

**Line 38 — vocabulary pill**
Current: `<span class="pill"><span data-plain>54 reserved words</span><span data-tech>19 verbs, 20 connectives</span></span>`
Updated: `<span class="pill"><span data-plain>58 reserved words</span><span data-tech>21 verbs, 22 connectives</span></span>`

**Line 80 — automated-checks count** (DECISION — see Style/Tone)
Current: `…It's well-tested: 1053 automated checks and 139 locked test sentences so behavior doesn't drift.`
Recommended: `…It's well-tested: 1303 automated checks and 139 locked test sentences so behavior doesn't drift.`

### `spec/index.html`

**Line 33 — status card**
Current (plain): `Status: v0.7.0. Current source has 54 reserved words, 139 locked test sentences, and 1160 pytest cases.`
Updated (plain): `Status: v0.8.0. Current source has 58 reserved words, 139 locked test sentences, and 1303 pytest cases.`
Current (tech): `Status: v0.7.0. The current pipeline supports … and the Meta-Structural Era's self-describing metadata (about/because/inherited).`
Updated (tech): `Status: v0.8.0. The current pipeline supports … the Meta-Structural Era's self-describing metadata (about/because/inherited), the Deontic Era's forbid/permit verbs, and the Temporal-Boundary Era's starting/until connectives.`

### `language/index.html`

**Line 7 — meta description**
Current: `…Liminate begins with 54 reserved words; expressiveness comes from composition and domain packs.`
Updated: `…Liminate begins with 58 reserved words; expressiveness comes from composition and domain packs.`

**Line 31 — lede (plain)**
Current: `Liminate starts with 54 reserved words. Power comes from combining them, not from piling on more.`
Updated: `Liminate starts with 58 reserved words. Power comes from combining them, not from piling on more.`

**Line 32 — lede (tech)**
Current: `Liminate begins with 54 reserved words: 19 verbs, 20 connectives, 8 operators, 3 articles, 1 declaration, 0 deferred reserved words, and the equal/multiplied/divided multi-word operator triggers.`
Updated: `Liminate begins with 58 reserved words: 21 verbs, 22 connectives, 8 operators, 3 articles, 1 declaration, 0 deferred reserved words, and the equal/multiplied/divided multi-word operator triggers.`

### `language/vocabulary/index.html`

**Lines 30–31 — page title (both modes)**
Current: `Fifty-four reserved words.`
Updated: `Fifty-eight reserved words.`

**Verbs row** — append `forbid`, `permit` after `require` (canonical order is `require`, `forbid`, `permit`, then `assign`):
Current: `…<code>require</code>, <code>assign</code>, <code>expect</code>, <code>sort</code>, <code>compare</code>, <code>transform</code>`
Updated: `…<code>require</code>, <code>forbid</code>, <code>permit</code>, <code>assign</code>, <code>expect</code>, <code>sort</code>, <code>compare</code>, <code>transform</code>`

**Connectives row** — append `starting`, `until` after `because`:
Current: `…<code>then</code>, <code>by</code>, <code>because</code>`
Updated: `…<code>then</code>, <code>by</code>, <code>because</code>, <code>starting</code>, <code>until</code>`

**Closing paragraphs** — the page currently ends the narrative with "the newest three words" (the Meta-Structural Era). Add one paragraph pair (plain + tech) after the Meta-Structural paragraphs, e.g.:

> **plain:** Four more words round out rules. `forbid` blocks something the way `require` demands it; `permit` simply records that something is allowed. `starting` and `until` give a rule a start date and an end date. The dates are just written down — the language stores them, a separate tool decides whether a rule is currently in force.

> **tech:** The Deontic Era added `forbid` (halts with `PROHIBITION_VIOLATED` on a true condition — the mirror of `require`) and `permit` (emits an informational line on a true condition, never halts), completing the require/forbid/permit triangle. The Temporal-Boundary Era added `starting`/`until`, statement-initial connectives attaching quoted ISO 8601 effective dates and sunset clauses as inert metadata; temporal evaluation is a product-layer concern, not interpreter runtime.

## New Pages (if any)

None. All updates are to existing pages.

## Style and Tone Notes

The liminate-site uses a paired `data-plain` / `data-tech` voice on most lines — a plain-language version for general readers and a precise technical version for practitioners. Every diff above preserves that pairing: update both variants. The site avoids marketing language and unbacked claims; all new copy here is drawn directly from the merged PRs and `vocabulary.py`. Keep the same restrained register — describe what the words do, not why they're exciting.

**Two test-metric decisions for Rob (do not resolve autonomously):**

1. **`139 locked test sentences`** appears on `index.html` (×2) and `spec/index.html`. This is a *different* metric from pytest case count and has been flagged in prior handoffs as ahead of the repo. The repo's README/DEV_README no longer cite a "locked test sentences" number. Recommendation: leave `139` untouched unless Rob has a current value; it is not a vocabulary count.
2. **pytest / automated-checks count** — the site shows `1160 pytest cases` (spec) and `1053 automated checks` (index line 80), both stale. Current is **1303**. Recommendation above updates both to 1303, but confirm Rob wants the homepage "automated checks" figure tracking the pytest total (they have historically been the same number).

## Do Not Change

- Anything under an `/archive/` path.
- The `philosophy/`, `learn/`, and `start/` narrative pages — they contain no vocabulary counts and the framing is correct as-is regardless of word count (verified: no stale count strings found there).
- The `deontic_mode` / `temporal_window` receipt-envelope documentation in `liminate-receipts/README.md` — already current; not a site concern.
- The "139 locked test sentences" figure — see decision 1 above; flag, do not silently rewrite.

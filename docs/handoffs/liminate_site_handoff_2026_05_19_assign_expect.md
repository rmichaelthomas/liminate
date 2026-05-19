# Liminate Site Update — Handoff Packet

**Date:** 2026-05-19
**Source:** PR #9 in `rmichaelthomas/liminate` (merge commit `15fe966`) — "feat: add `assign`/`expect` — delegated + epistemic eras (42 → 44)". This is batch 3 in a vocabulary-strategy walkthrough that also added `weakens`/`over` (batch 1) and `require`/`then` (batch 2). The site is currently pinned to the **pre-batch-1** vocabulary numbers, so this handoff brings it forward across all three batches in one pass.
**Scope:** Vocabulary expanded from **35 → 44 reserved words** (11 → 16 verbs, 14 → 18 connectives). The new verbs are `weakens`, `require`, `assign`, `expect`. The new connectives are `over`, `then`. The test count has grown from 835 → 972 pytest cases. The "139 locked test sentences" pill on the home page should be reviewed — the core repo's own README and DEV_README currently say "127 locked test sentences," so the site is ahead of the repo on this number. Flag with Rob; do not change autonomously.

---

## Pages Requiring Updates

| Page | Path | What to change |
|---|---|---|
| Home (hero pills) | `index.html` | Three pills are stale: tests passing, the reserved-word count, and the verbs/connectives count. |
| Spec / repos | `spec/index.html` | The "Interpreter repository" card's plain-English status sentence cites the reserved-word, test-sentence, and pytest-case numbers inline. Update the reserved-word and pytest counts; flag the 139-sentence number for Rob. |
| Language | `language/index.html` | The page lede in both modes cites "35 reserved words"; tech mode also gives the verb/connective breakdown. Meta description and the vocabulary list item both repeat "35". |
| Vocabulary | `language/vocabulary/index.html` | Page title, lede, meta description, and the verb-and-connective tables are all stuck at the pre-batch-1 enumeration. This is the largest single edit and should pick up the new four verbs and two connectives in the right cells. |

---

## Content Diffs

### `index.html` (hero pills, around line 36–38)

**Current text:**
```html
<span class="pill"><span data-plain>835 tests passing</span><span data-tech>835 pytest cases</span></span>
<span class="pill"><span data-plain>139 locked test sentences</span><span data-tech>139 locked test sentences</span></span>
<span class="pill"><span data-plain>35 reserved words</span><span data-tech>11 verbs, 14 connectives</span></span>
```

**Updated text:**
```html
<span class="pill"><span data-plain>972 tests passing</span><span data-tech>972 pytest cases</span></span>
<span class="pill"><span data-plain>139 locked test sentences</span><span data-tech>139 locked test sentences</span></span>
<span class="pill"><span data-plain>44 reserved words</span><span data-tech>16 verbs, 18 connectives</span></span>
```

Note: the "139 locked test sentences" pill is **not** changed in this diff. The core repo's README and DEV_README both say "127 locked test sentences" today, so the website is *ahead* of the source. Either the site pill was incremented in anticipation of new sentences that never got merged, or the README is behind. **Surface this to Rob as a question before changing.** Do not silently reconcile.

### `spec/index.html` (Interpreter repository card, around line 33)

**Current text:**
```html
<p data-plain>Status: v0.2.0. Current source has 35 reserved words, 139 locked test sentences, and 835 pytest cases.</p>
```

**Updated text:**
```html
<p data-plain>Status: v0.2.0. Current source has 44 reserved words, 139 locked test sentences, and 972 pytest cases.</p>
```

Same flag as above for "139 locked test sentences."

### `language/index.html` (lede and list, lines 7, 31–34)

**Current text (meta description, line 7):**
```html
<meta name="description" content="The language is bounded. Liminate begins with 35 reserved words; expressiveness comes from composition and domain packs.">
```

**Updated text:**
```html
<meta name="description" content="The language is bounded. Liminate begins with 44 reserved words; expressiveness comes from composition and domain packs.">
```

**Current text (lede + list, lines 31–34):**
```html
<p class="lede" data-plain>Liminate starts with 35 reserved words. Power comes from combining them, not from piling on more.</p>
<p class="lede" data-tech>Liminate begins with 35 reserved words: 11 verbs, 14 connectives, 4 operators, 3 articles, 2 deferred reserved words, and the <code>equal</code> operator trigger.</p>
<ul class="index-list">
  <li><a href="vocabulary/">Vocabulary</a><span data-plain>The 35 words and what each kind does.</span><span data-tech>Verbs, connectives, operators, articles, future reserved words.</span></li>
```

**Updated text:**
```html
<p class="lede" data-plain>Liminate starts with 44 reserved words. Power comes from combining them, not from piling on more.</p>
<p class="lede" data-tech>Liminate begins with 44 reserved words: 16 verbs, 18 connectives, 4 operators, 3 articles, 2 deferred reserved words, and the <code>equal</code> operator trigger.</p>
<ul class="index-list">
  <li><a href="vocabulary/">Vocabulary</a><span data-plain>The 44 words and what each kind does.</span><span data-tech>Verbs, connectives, operators, articles, future reserved words.</span></li>
```

### `language/vocabulary/index.html` (title, lede, meta, table)

**Current text (meta description, line 7):**
```html
<meta name="description" content="Thirty-five reserved words. No other words are part of the base language except user-provided names and literal values.">
```

**Updated text:**
```html
<meta name="description" content="Forty-four reserved words. No other words are part of the base language except user-provided names and literal values.">
```

**Current text (page title, lines 30–31):**
```html
<h1 class="page-title" data-plain>Thirty-five reserved words.</h1>
<h1 class="page-title" data-tech>Thirty-five reserved words.</h1>
```

**Updated text:**
```html
<h1 class="page-title" data-plain>Forty-four reserved words.</h1>
<h1 class="page-title" data-tech>Forty-four reserved words.</h1>
```

**Current text (category table, lines 35–36):**
```html
<tr><td>Verbs</td><td><code>remember</code>, <code>show</code>, <code>filter</code>, <code>keep</code>, <code>count</code>, <code>gather</code>, <code>combine</code>, <code>each</code>, <code>choose</code>, <code>finish</code>, <code>add</code></td></tr>
<tr><td>Connectives</td><td><code>where</code>, <code>and</code>, <code>or</code>, <code>from</code>, <code>with</code>, <code>called</code>, <code>to</code>, <code>how</code>, <code>as</code>, <code>of</code>, <code>if</code>, <code>otherwise</code>, <code>when</code>, <code>unless</code></td></tr>
```

**Updated text:**
```html
<tr><td>Verbs</td><td><code>remember</code>, <code>show</code>, <code>filter</code>, <code>keep</code>, <code>count</code>, <code>gather</code>, <code>combine</code>, <code>each</code>, <code>choose</code>, <code>finish</code>, <code>add</code>, <code>remove</code>, <code>weakens</code>, <code>require</code>, <code>assign</code>, <code>expect</code></td></tr>
<tr><td>Connectives</td><td><code>where</code>, <code>and</code>, <code>or</code>, <code>from</code>, <code>with</code>, <code>called</code>, <code>to</code>, <code>how</code>, <code>as</code>, <code>of</code>, <code>if</code>, <code>otherwise</code>, <code>when</code>, <code>unless</code>, <code>includes</code>, <code>within</code>, <code>over</code>, <code>then</code></td></tr>
```

Verb ordering follows the order they appear in `src/liminate/vocabulary.py`'s `VERBS` frozenset — by inception batch — so new readers see the historical accretion. The new four (`remove`, `weakens`, `require`, `assign`, `expect`) sit at the end. Connectives likewise: `includes`, `within`, `over`, `then` go at the end.

Note: this table also lists Operators / Articles / Future reserved / Syntax marker rows. Those rows are unchanged and should not be touched.

---

## What the new words mean (so the writer doesn't have to dig)

The site's vocabulary page is currently terse — just the word lists, no per-word descriptions. That's fine; no per-word copy is required by this handoff. But for context, in case the writer wants to add a follow-up explainer page:

| Word | Kind | One-line meaning |
|---|---|---|
| `remove` | verb | Retracts an item from a list (mirror of `add`; errors if not found). |
| `weakens` | verb | Attaches autonomous linear decay to a numeric value — falls to zero over a stated period of ticks. |
| `require` | verb | Evaluates a condition; halts with `REQUIREMENT_NOT_MET` if it fails (silent on pass). |
| `assign` | verb | Stores an item-to-recipient mapping (`assign review-task to "compliance-team"`). |
| `expect` | verb | Like `require`, but emits a divergence output line on failure and continues with `SUCCESS` — informational, non-halting. |
| `over` | connective | Introduces the decay period in `weakens` (`weakens energy over 10`). |
| `then` | connective | Declared sequencing between operations (`add ... then require ...`), same shape as `and` but with stated ordering intent. |

These align with the "era" framing the architect has been using — `weakens` is Metabolic, `require`/`then` are Normative, `assign` is Delegated, `expect` is Epistemic. The site does not currently use that framing and **this handoff does not introduce it.** If a future explainer page wants to organize by era, that is a separate editorial decision.

---

## New Pages (if any)

None for this propagation. The vocabulary expansion fits inside the existing page structure.

---

## Style and Tone Notes

The liminate-site uses a **two-mode pattern** throughout: every prose paragraph has a `data-plain` (Plain English) version and a `data-tech` (Technical) version, toggled by a mode switch at the top of each page. When updating numbers, **always update both versions** — the diffs above already show both where they exist, but if you find another instance of the stale count, check for its sibling.

The site's voice is deliberately understated. No exclamation marks, no marketing language ("powerful", "amazing", "revolutionary"). Phrases like "bounded vocabulary" and "the prose IS the program" are load-bearing — they appear repeatedly and shouldn't be paraphrased. The four-verb / two-connective addition is a quiet bump, not an announcement.

Do not introduce any claim that isn't backed by the merged code. The era framing (Metabolic / Normative / Delegated / Epistemic) is internal architecture vocabulary — it exists in the core repo's DEV_README and commit messages but is not user-facing site copy.

---

## Do Not Change

- Any pill, page, or paragraph that does not currently contain one of the stale numbers (`35`, `11`, `14`, `835`).
- The "139 locked test sentences" pill on `index.html` and the equivalent in `spec/index.html` — flag for Rob first, since the core repo says 127.
- The "two-mode" content infrastructure (`data-plain` / `data-tech` spans) — preserve the pattern exactly when editing.
- The Operators / Articles / Future reserved / Syntax marker rows in the vocabulary table — unchanged by this propagation.
- Any page under `learn/`, `philosophy/`, `start/`, `install/`, or `skills/` — none of those currently cite the vocabulary count, and the spot-check during repo scanning confirmed it.
- Archival pages, historical references, or any content that names a prior locked count as historical context (none found, but flagged as a guard).

---

## Verification after the edits

After applying the diffs, run:

```bash
grep -rEn "\b(35|11 verbs|14 connectives|835)\b" liminate-site/ \
    --include="*.html" | grep -v "node_modules"
```

The output should be empty for the three numeric strings that appear in the diffs (`35`, `11 verbs`, `14 connectives`, `835`). If anything remains, it's drift this handoff missed — surface it.

---

## Provenance

Generated by the `liminate-docs-propagation` skill on 2026-05-19, working from PR #9 (`feat/assign-expect-delegated-epistemic`, merged as `15fe966`) and a full scan of `~/liminate-site/` for the stale numeric strings. Counts cross-checked against `src/liminate/vocabulary.py` on `main` at the same commit: `len(VERBS) == 16`, `len(CONNECTIVES) == 18`, `len(ALL_RESERVED) == 44`. Test count is `pytest tests/` output on `main` post-merge.

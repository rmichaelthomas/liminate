# Liminate Site Update — Handoff Packet

**Date:** 2026-05-19
**Source:** Merged PRs #11 (arithmetic operators), #12 (`sort`/`reverse`), #13 (`compare`), #14 (`transform`) on `rmichaelthomas/liminate` `main`. Net vocabulary change: **44 → 51 reserved words**.
**Scope:** Verbs 16 → 19 (`sort`, `compare`, `transform`); connectives 18 → 19 (`by`); single-word operators 4 → 7 (`plus`, `minus`, `reverse`); multi-word trigger words 1 → 3 (`equal`, `multiplied`, `divided`); **`V2_RESERVED` is now empty** — `transform` and `compare` were the last deferred words. New features: arithmetic expressions with PEMDAS precedence, in-place `sort`, structured `compare`, per-element `transform`.

Per Rob's propagation decision, status values are refreshed alongside vocabulary: **version v0.2.0 → v0.3.0** and **972 → 1053 pytest cases**. The "locked test sentences" count (139 on the site) is a curated metric — leave it at 139 unless you can verify the current curated total; the repo README was left at its own 127 for the same reason.

## Pages Requiring Updates

| Page | Path | What to change |
|---|---|---|
| Home | `index.html` | Pills: version, test count, reserved-word/verb/connective counts. Body prose test counts. |
| Spec | `spec/index.html` | Status line: version, reserved-word count. |
| Language | `language/index.html` | Meta description + two lede lines: reserved-word counts and the category breakdown. |
| Vocabulary | `language/vocabulary/index.html` | Page title, verb/connective/operator rows, remove the "Future reserved" row. |

## Content Diffs

### `index.html`

**L35 — current:**
```html
    <span class="pill"><span data-plain>v0.2.0</span><span data-tech>v0.2.0</span></span>
```
**Updated:**
```html
    <span class="pill"><span data-plain>v0.3.0</span><span data-tech>v0.3.0</span></span>
```

**L36 — current:**
```html
    <span class="pill"><span data-plain>972 tests passing</span><span data-tech>972 pytest cases</span></span>
```
**Updated:**
```html
    <span class="pill"><span data-plain>1053 tests passing</span><span data-tech>1053 pytest cases</span></span>
```

**L38 — current:**
```html
    <span class="pill"><span data-plain>44 reserved words</span><span data-tech>16 verbs, 18 connectives</span></span>
```
**Updated:**
```html
    <span class="pill"><span data-plain>51 reserved words</span><span data-tech>19 verbs, 19 connectives</span></span>
```

**L80 — current:**
> ...It's well-tested: 972 automated checks and 139 locked test sentences so behavior doesn't drift.

**Updated:** change `972` → `1053` (leave `139` unless verified).

**L81 — current:**
> ...pressure-tested against 972 pytest cases and 139 frozen sentences.

**Updated:** change `972` → `1053` (leave `139` unless verified).

> **Note:** L37 (`139 locked test sentences`) — leave unless the curated sentence total is reconfirmed.

### `spec/index.html`

**L33 — current (`data-plain`):**
> Status: v0.2.0. Current source has 44 reserved words, 139 locked test sentences, and 972 pytest cases.

**Updated:**
> Status: v0.3.0. Current source has 51 reserved words, 139 locked test sentences, and 1053 pytest cases.

(`data-tech` half of L33 has no vocabulary/version-specific numbers beyond "five execution types," which is unchanged — leave it.)

### `language/index.html`

**L7 — current:**
```html
<meta name="description" content="The language is bounded. Liminate begins with 44 reserved words; expressiveness comes from composition and domain packs.">
```
**Updated:** `44` → `51`.

**L31 — current (`data-plain`):**
> Liminate starts with 44 reserved words. Power comes from combining them, not from piling on more.

**Updated:** `44` → `51`.

**L32 — current (`data-tech`):**
> Liminate begins with 44 reserved words: 16 verbs, 18 connectives, 4 operators, 3 articles, 2 deferred reserved words, and the `equal` operator trigger.

**Updated:**
> Liminate begins with 51 reserved words: 19 verbs, 19 connectives, 7 operators, 3 articles, 0 deferred reserved words, and the `equal`/`multiplied`/`divided` multi-word operator triggers.

### `language/vocabulary/index.html`

**L30–L31 — current (page title, both modes):**
```html
<h1 class="page-title" data-plain>Forty-four reserved words.</h1>
<h1 class="page-title" data-tech>Forty-four reserved words.</h1>
```
**Updated:** `Forty-four` → `Fifty-one` (both lines).

**L35 — Verbs row, current:**
```html
<tr><td>Verbs</td><td><code>remember</code>, <code>show</code>, <code>filter</code>, <code>keep</code>, <code>count</code>, <code>gather</code>, <code>combine</code>, <code>each</code>, <code>choose</code>, <code>finish</code>, <code>add</code>, <code>remove</code>, <code>weakens</code>, <code>require</code>, <code>assign</code>, <code>expect</code></td></tr>
```
**Updated:** append `, <code>sort</code>, <code>compare</code>, <code>transform</code>` before `</td>`.

**L36 — Connectives row, current:** ends with `..., <code>over</code>, <code>then</code></td></tr>`
**Updated:** append `, <code>by</code>` before `</td>`.

**L37 — Operators row, current:**
```html
<tr><td>Operators</td><td><code>is</code>, <code>above</code>, <code>below</code>, <code>not</code>, plus <code>equal</code> for the <code>equal to</code> phrase</td></tr>
```
**Updated:**
```html
<tr><td>Operators</td><td><code>is</code>, <code>above</code>, <code>below</code>, <code>not</code>, <code>plus</code>, <code>minus</code>, <code>reverse</code>, plus <code>equal</code>/<code>multiplied</code>/<code>divided</code> for the <code>equal to</code>, <code>multiplied by</code>, and <code>divided by</code> phrases</td></tr>
```

**L39 — Future-reserved row, current:**
```html
<tr><td>Future reserved</td><td><code>transform</code>, <code>compare</code></td></tr>
```
**Updated:** **remove this row entirely.** `V2_RESERVED` is now empty; both words are active verbs (already listed in the Verbs row).

## New Pages (if any)

None required. Optionally, the Language or Vocabulary page could gain a short "Arithmetic" note (the four operators + PEMDAS) and a one-line mention of `sort`/`compare`/`transform`, mirroring the new sections in the repo's `docs/language/syntax.md` — but this is enrichment, not a stale-content fix.

## Style and Tone Notes

The site uses a dual-mode voice: every content element carries `data-plain` (accessible, jargon-free) and `data-tech` (precise, terminology-forward) variants, toggled by the reading-mode switch. Keep both variants in sync when editing. The tone is plain, declarative, non-marketing — "the sentence is the program," no hype. Match it. Do not introduce claims not backed by the merged PRs.

## Do Not Change (false positives — these are unrelated to this propagation)

- `install/index.html` L71, `examples/packs/index.html` L31, `language/pipeline/index.html` L43 — these reference `compare_values`, the **pack execution type**, not the base `compare` verb. Leave unchanged.
- `skills/index.html` L54, `skills/why-agents/index.html` L44 — these reference `transform` as one of the **prosecode-prompt-compiler's seven intent-IR verbs**, not Liminate's `transform` verb. Leave unchanged.
- Any archival/historical content, philosophical framing, or the `139 locked test sentences` count (unless independently reconfirmed).

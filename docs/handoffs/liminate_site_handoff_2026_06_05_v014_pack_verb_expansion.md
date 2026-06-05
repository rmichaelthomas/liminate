# Liminate Site Update — Handoff Packet

**Date:** June 5, 2026
**Source:** Git commits v0.11.0 → v0.14.0 on `liminate@main` (PRs #41–#44, plus the v0.13.0 version bump). Source of truth: `src/liminate/vocabulary.py` (58 reserved words, **unchanged**), `liminate --version` → `0.14.0`, `pytest tests/` → **1456 passing** (per the `feat: fit verb` commit message: "Full suite 1456 passed").
**Scope:** Version v0.11.0 → v0.14.0. Vocabulary unchanged at 58 words / 21 verbs / 22 connectives. Test count 1339 → 1456. Capability additions are **runtime and pack-layer only** — no base-vocabulary growth: `PACK_VERB_FAILURE` result status + inherited `when` blocks (v0.12); empty-list construction + descending/step-valued ranges (v0.12); literal-valued composition parameters (D-1); analyzer-time deontic contradiction detection (D-4); `range_check` execution + `validate` pack verb (D-8); timer-driven decay tick advancement (D-7); `conformance_check` execution + `fit` pack verb + iterable pack verbs (v0.14). The pack-verb execution union grew from five to **eight** types.

---

## ⚠️ Target repo — read first

Per current deployment topology, **`liminate-site` is archived and must NOT be edited.** The live website is served from **`liminate-dev`** (the consolidated products + site deployment at `liminate.dev`). Apply these changes in `liminate-dev`, not in the archived `liminate-site`.

**`liminate-dev` was not cloned locally during this propagation**, so the "Current" strings below are carried forward from the prior handoff (`liminate_site_handoff_2026_05_28_v011_public_api.md`), which set the site to v0.11.0 / 1339. **Verify each "Current" string against the live `liminate-dev` source before replacing** — if the site drifted from the v0.11 baseline, adjust the find-target accordingly. Page paths below mirror the archived `liminate-site` layout and may differ in `liminate-dev`; confirm the actual paths.

---

## Pages Requiring Updates

| Page | Path (verify in liminate-dev) | What to change |
|---|---|---|
| Homepage | `index.html` | Version pill: `v0.11.0` → `v0.14.0`; automated-checks count: `1339` → `1456` |
| Spec | `spec/index.html` | Status line (plain + tech): version `v0.11.0` → `v0.14.0`, pytest `1339` → `1456`, append Pack-Verb Expansion Era clause |

---

## Content Diffs

### `index.html` — version pill

**Current:**
```html
<span class="pill"><span data-plain>v0.11.0</span><span data-tech>v0.11.0</span></span>
```

**Updated:**
```html
<span class="pill"><span data-plain>v0.14.0</span><span data-tech>v0.14.0</span></span>
```

### `index.html` — automated checks count

The homepage references the pytest count in a sentence like "It's well-tested: 1339 automated checks and 139 locked test sentences so behavior doesn't drift."

**Updated:** Replace `1339` with `1456`. Locked-sentence count (139) — **see "Verify before applying" below**; carry forward unchanged unless verification shows otherwise.

### `spec/index.html` — status line (plain)

**Current (plain):**
`Status: v0.11.0. Current source has 58 reserved words, 139 locked test sentences, and 1339 pytest cases.`

**Updated (plain):**
`Status: v0.14.0. Current source has 58 reserved words, 139 locked test sentences, and 1456 pytest cases.`

### `spec/index.html` — status line (tech)

Append to the existing tech status line, **after the Public API Era clause (v0.11)**:

> … `enter_phase2` lets static inspectors skip the reactive listener; every result carries `line`/`source`/`timestamp`/`duration_ms` metadata (v0.11). **Pack-Verb Expansion Era (v0.12–v0.14):** `PACK_VERB_FAILURE` is a dedicated result status carrying structured failure metadata, and pack-verb `when` blocks can be inherited; three new pack-verb execution types ship — `numeric_extract_compare`, `range_check` (surfaced as the `validate` pack verb), and `conformance_check` (surfaced as the `fit` pack verb) — bringing the execution union to eight; pack verbs become iterable via `each` in pack slots; the base language gains empty-list construction and descending/step-valued ranges; composition parameters accept literal values; deontic contradictions are detected at analyze time; and timer packs can drive autonomous decay-tick advancement. The base 58-word vocabulary is untouched — every addition is runtime or pack-layer.

---

## Verify before applying

These could not be confirmed against `liminate-dev` (not cloned locally). Confirm before applying:

1. **Live "Current" strings.** The find-targets above assume the site is at the v0.11.0 / 1339 baseline. If `liminate-dev` drifted, adjust.
2. **Page paths.** `index.html` and `spec/index.html` paths are from the archived `liminate-site`; confirm equivalents in `liminate-dev`.
3. **Locked test-sentence count (139).** No evidence in this delta that new *spec* sentences were locked (the +15 from the `fit` verb are pytest cases, not necessarily locked spec sentences). Carry 139 forward unchanged unless `docs/spec/` in core shows a new count. Do **not** invent a new number.

---

## Style and Tone Notes

`liminate-dev` (and the archived `liminate-site` before it) uses spare, functional prose — no marketing language, no hype. Feature descriptions name the capability and its behavioral contract (what it does, what halts, what emits), not benefits or adjectives. Match that register.

The Pack-Verb Expansion additions are domain-pack and runtime infrastructure, not user-facing language changes. Frame them as facts ("the pack-verb execution union is now eight types; the base vocabulary is unchanged"), not as selling points. The most important framing fact: **the base 58-word vocabulary did not grow** — expressiveness scaled through the pack-verb contract, exactly as the language's design thesis predicts.

## Do Not Change

- Vocabulary pill (`58 reserved words`, `21 verbs`, `22 connectives`) — vocabulary is unchanged across v0.12–v0.14.
- Locked test-sentence count (139) — unchanged absent spec evidence (see "Verify before applying").
- Philosophy page — not affected by these releases.
- `learn/`, `start/`, `language/` tutorial pages — no base-grammar changes that affect tutorial examples.
- The archived `liminate-site` repo itself — do not edit it; it is superseded by `liminate-dev`.
- Any archival or checkpoint documents.

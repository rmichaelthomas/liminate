# Liminate Site Update — Handoff Packet

**Date:** May 28, 2026
**Source:** Git commits v0.9.0 → v0.11.0 on `liminate@main` (PRs #35–#40). Source of truth: `src/liminate/vocabulary.py` (58 reserved words, unchanged), `liminate --version` → `0.11.0`, `pytest tests/` → 1339 passing.
**Scope:** Version v0.8.0 → v0.11.0. Vocabulary unchanged at 58 words / 21 verbs / 22 connectives. Test count 1303 → 1339. Three capability additions: `require each` grammar extension (v0.9), Platform Era infrastructure (v0.10), Public API `run()` / `ContractResult` / `enter_phase2` (v0.11).

---

## Pages Requiring Updates

| Page | Path | What to change |
|---|---|---|
| Homepage | `index.html` | Version pill: `v0.8.0` → `v0.11.0`; automated-checks count: `1303` → `1339` |
| Spec | `spec/index.html` | Status line: version, test count, add new era descriptions |

---

## Content Diffs

### `index.html` — version pill

**Current:**
```html
<span class="pill"><span data-plain>v0.8.0</span><span data-tech>v0.8.0</span></span>
```

**Updated:**
```html
<span class="pill"><span data-plain>v0.11.0</span><span data-tech>v0.11.0</span></span>
```

### `index.html` — automated checks count

The homepage references the pytest count in a sentence like "It's well-tested: 1303 automated checks and 139 locked test sentences so behavior doesn't drift."

**Updated:** Replace `1303` with `1339`. Locked sentence count (139) is unchanged.

### `spec/index.html` — status line (plain)

**Current (plain):**
`Status: v0.8.0. Current source has 58 reserved words, 139 locked test sentences, and 1303 pytest cases.`

**Updated (plain):**
`Status: v0.11.0. Current source has 58 reserved words, 139 locked test sentences, and 1339 pytest cases.`

### `spec/index.html` — status line (tech)

Append to the existing tech status line (after the Temporal-Boundary Era clause):

> … the Temporal-Boundary Era's `starting`/`until` connectives. `require each` grammar extension — `require <name> each <list>` iterates enforcement over a list with a named binding, halting at the first violation (v0.9). Platform Era: non-zero exit on interpreter errors, `--help`/`-h` flag, CI test/pack-sync workflow, VERSIONING.md replay guarantee (v0.10). Public API Era: `run(source, ...)` is now the single shared program-execution entry point for the CLI and Receipts, returning a `ContractResult`; `enter_phase2` lets static inspectors skip the reactive listener; every result carries `line`/`source`/`timestamp`/`duration_ms` metadata (v0.11).

---

## Style and Tone Notes

The liminate-site uses spare, functional prose — no marketing language, no hype. Feature descriptions name the capability and its behavioral contract (what it does, what halts, what emits), not benefits or adjectives. Match that register for the new era descriptions.

The Public API addition is significant but does not change the user-facing language. Frame it as an infrastructure fact ("the CLI and Receipts now share a single execution loop") rather than as a selling point.

## Do Not Change

- Vocabulary pill (`58 reserved words`, `21 verbs`, `22 connectives`) — vocabulary is unchanged across v0.9–v0.11.
- Locked test sentence count (139) — unchanged.
- Philosophy page — not affected by these releases.
- `learn/` and `start/` pages — no grammar changes that affect the tutorial examples.
- Any archival or checkpoint documents.

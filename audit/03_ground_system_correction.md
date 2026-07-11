# 03 — Ground System Correction Block

**Audit:** Liminate ecosystem — Phase 1 UX Coherence FIX PASS
**Run date:** 2026-07-10
**Purpose:** Record the correction to the locked ground-system description per decision #4 (locked with Rob in the Phase 1 decision walkthrough) and finding F1-10 (`audit/phase1_ux_coherence_findings.md`), without silently rewriting the original locked text. Immutable-addenda discipline: this is an addendum, not an edit to the original.

## Provenance note — source document not located

F1-10 cites `Locked reference violated: §4.1 — "Ink (`#0B1C38`, Agreements)."` as the origin of the stale ground description. This build pass searched the vault (semantic search across `liminate_checkpoint_v10_public_surface_unification_and_website_chain.md`, `liminate_unified_positioning_document.md` §7.2, and targeted queries for "Ink ground Agreements locked," "gn-ink gn-paper," and "four grounds by design") and did not find a single document whose own numbering matches "§4.1" with that exact clause. The unified positioning document (May 23, 2026) has a different §4 entirely (proof points, not grounds) and predates Seshat/Translate/Sentinels. The closest visual-identity table found — §7.2 of that document — lists only Paper and Night, not Ink or Seshat-amber, confirming it is an earlier ancestor of whatever document F1-10 actually cites, not that document itself.

**This correction is therefore recorded here, in the repo, as the durable artifact** — the same durable-record role `02_remediation_tracker.md` plays for Phase 0. If the original locked document is later located, this block should be appended there too (or a pointer added here), not deleted.

## The correction

**Old locked description (per F1-10's citation):** "Ink (`#0B1C38`, Agreements)" — Ink named as a single-product ground.

**Deployed reality, confirmed live this session:** three of five products share Ink — Agreements, Translate, and Sentinels (`agreements.html`/`agreements-app.html`, `translate.html`/`translate-app.html`, `sentinels.html`/`sentinels-app.html` all render `body { background: var(--ink) }` with the `gn-ink` nav modifier). Receipts' app (`index.html`, at `/receipts/app`) also renders on Ink via its plain `.gn` nav (no ground modifier class), while the Receipts *landing* (`landing.html`) and case studies render on Night. Paper carries the homepage, constellation pages, and legal pages. Seshat is its own bespoke amber-dark ground (`--ground: #1E1206` in `seshat.html`), never Ink, Paper, or Night.

**Corrected, locked description — FOUR-GROUNDS-BY-DESIGN (decision #4, this session):**

| Ground | Hex | Carries |
|---|---|---|
| Night | `#111018` | Default. Receipts landing, case studies. |
| Paper | `#F5F1E8` | Homepage, constellation pages, legal pages. |
| Ink | `#0B1C38` | The platform apps — Translate, Agreements, Sentinels, Receipts (`/receipts/app`). |
| Seshat-amber | `#1E1206` | Seshat, the local product. Bespoke, never shared. |

This is intentional, not drift — it is one of the three purposeful divergences this build pass is required to preserve, alongside the TUI's terminal-safe glyph set and the Seshat landing's hieroglyphic register (see the build prompt's §1 rule and §6 invariant 7). **No surface was repainted to produce this correction.** It is a documentation fix only: the description now matches what is already deployed, rather than the deployed system being changed to match a two-year-old description.

## Status

`OPEN → CORRECTED (documentation only)`. No code changed under this finding. If Rob identifies the actual `§4.1` source document, append a pointer from that document to this correction (or fold this block into it) rather than deleting this record.

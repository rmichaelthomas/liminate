# Liminate Site Update — Handoff Packet

**Date:** 2026-05-22
**Source:** Liminate Receipts Checkpoint v5 §16 Phase C — Receipt Line Envelope Fields. Shipped in `liminate-receipts` PR #9 (merged to `main`). Source of truth: `liminate-receipts/app/serializers.py`.
**Scope:** Four new fields added to the per-line `meta` envelope of a Receipts receipt line — `deontic_mode`, `temporal_window`, `rationale`, `provenance` — surfacing the four Liminate vocabulary eras (deontic verbs, `starting`/`until`, `because`, `inherited`) at the receipt level. Data population only; no frontend rendering yet.

## Pages Requiring Updates

**None.**

The Phase C change is confined to the `liminate-receipts` JSON output shape. A scan of `liminate-site` (May 22, 2026) found **no page that documents the Receipts API, the receipt line structure, or the `meta` envelope**. The site documents the language and vocabulary, not the Receipts service's output format. There is therefore nothing on the site to update for this change.

The four vocabulary eras these fields surface (`require`/`forbid`/`permit`, `starting`/`until`, `because`, `inherited`) were already documented on the site during the Meta-Structural Era pass — see `liminate_site_handoff_2026_05_21_meta_structural.md`. Phase C adds no new vocabulary; it only exposes existing vocabulary in the receipt envelope.

## Content Diffs

None.

## New Pages (if any)

None.

## Style and Tone Notes

N/A for this pass. If a Receipts service page is added to the site in future (it does not exist today), the `meta` envelope table now documented in `liminate-receipts/README.md` is the canonical reference for field names, presence rules, and value sets. Match the site's paired `data-plain` / `data-tech` voice and avoid implying the four fields are rendered in the UI — as of this packet they are populated in the data only; frontend rendering is a deferred follow-up.

## Do Not Change

- Any existing site page — this change requires no site edits.
- The prior handoff packets in `docs/handoffs/` — historical records, not to be modified.

## Repo Propagation Record

| Repo | Action taken |
|---|---|
| `liminate` (core) | No change — vocabulary unchanged by Phase C. |
| `liminate-receipts` | `README.md` — documented the per-line `meta` envelope (all six fields) in the API section; corrected stale interpreter version `v0.7.0` → `v0.7.1`. Branch `docs/propagate-phase-c-meta-envelope`. |
| `liminate-session-contracts` | No change — does not document the Receipts envelope. |
| `liminate-contract-inheritance` | No change. |
| `prosecode-prompt-compiler` | No change. |
| `prosecode-context-pager` | No change. |
| `prosecode-handoff-packet` | No change. |
| `liminate-site` | No change — no Receipts/envelope page exists. |

# COBOL → Liminate — Three-Run Comparison (Run 1 vs Run 2 vs Run 3)

This document is written **after** the Run 3 finding was complete (§7), so the
blind structure that protects the currency-hypothesis test is preserved.

## 1. Three-way table

| Dimension | Run 1 | Run 2 | Run 3 (pilot) |
|---|---|---|---|
| Corpus | 3 curated repos (learn_cobol, cobol-samples, mortgagesample) | X-COBOL 2024 (5,195 files), *identity unverified* | X-COBOL 2024 (5,195 files), **identity verified** (Zenodo 14269462) |
| Selection | 3 hand-picked teaching/sample repos | full sweep (2,282 files triaged) | **business/finance-leaning pilot** (13 repos scanned, 6 read deeply) |
| Rules attempted | 32 | 520 | 22 |
| Duplicates collapsed | — | 249 | 0 |
| **Expressibility — base** | 18 (56.3%) | 204 (39.2%) | 19 (**86.4%**) |
| **Expressibility — pack-needed** | 13 (40.6%) | 279 (53.7%) | 3 (13.6%) |
| **Expressibility — untranslatable** | 1 (3.1%) | 37 (7.1%) | 0 (0%) |
| Top pack demands | currency/rounding/decimal cluster (~7 of 13 labels) | exponentiation 91, substring 72, collation 61, currency-rounding 19 | date-arithmetic 2, exponentiation 1 |
| **Boundary fidelity events** | 22 | **0** (classifier bug) | **11** |
| Other fidelity events | rounding 11, type-coercion 9, precedence 5, none 5, truncation 3, sign 2 | none 241, precedence 91, type-coercion 82, truncation 73, rounding 33, **boundary 0** | none 6, precedence 4, sign 3, rounding 2 |
| Verb frequency | remember 16, permit 10, forbid 3, require 2 | permit 132, forbid 41, remember 31 | remember 19, forbid 8, permit 5, require 2 |

## 2. Currency-hypothesis test

**Run 1's claim:** currency / `ROUNDED` / packed-decimal handling was the
dominant pack demand — roughly **7 of 13** Run 1 pack labels named currency,
rounded, decimal-precision, or size-error/overflow concerns.

**Deciding numbers for the currency cluster** (`currency-rounding` +
`decimal-scale` + `size-error-overflow`):

| Run | Currency-cluster pack demand | As share of pack-needed |
|---|---|---|
| Run 1 | ~7 of 13 labels | ~54% (dominant) |
| Run 2 | 19 + 14 + 1 = **34** | 34 / 279 = **12.2%** |
| Run 3 (pilot) | 0 explicit pack-needed | 0 / 3 = **0%** |

**Verdict: Run 3 weakens the currency hypothesis — consistent with Run 2 —
but with low statistical power and an important nuance.**

- In the *full* 2024 corpus (Run 2), the dominant pack demands were
  **exponentiation, substring-predicate, and string-collation**, not currency.
  Currency-cluster demand was a modest 12%.
- In the Run 3 business-leaning pilot, *no* rule needed a currency pack to be
  expressed at all. Instead, currency precision surfaced as **fidelity risk**:
  2 of 19 base rules (R0012, R0021) are fully expressible as arithmetic but
  carry a `rounding` event because base Liminate cannot reproduce COBOL's
  `ROUNDED` half-up step.
- So the refined reading across runs: **currency is not where Liminate hits an
  expressibility wall — it is where it incurs a fidelity cost.** Run 1's
  "currency dominates" was an artifact of a tiny, finance-curated corpus
  (mortgage + invoice samples). The broader, verified corpus does not bear it
  out. (Caveat: the Run 3 pilot has only 3 pack-needed rules — too few to carry
  the claim alone; it corroborates Run 2 rather than standing on its own.)

## 3. Run 2 vs Run 3 reconciliation

**Run 3 supersedes Run 2** as the authoritative result; Run 2 is retained as a
record. Two things changed:

1. **Corpus identity is now verified.** Run 2's header literally hedged:
   *"14269462 inferred from 5,195-file corpus; local zenodo_record.json still
   reports 7968845."* Run 3's §2 gate caught that exact contradiction, the
   maintainer removed the stale 2023 metadata and confirmed the 2024 upload,
   and the corpus is now pinned to **Zenodo 14269462** with a content
   fingerprint. **Run 2's inference turned out to be correct** — Run 2 and
   Run 3 run against the *same* 2024 corpus — but Run 2 could not prove it, and
   an experiment about verification cannot rest on a guess.

2. **The fidelity model is rebuilt.** Run 2 emitted exactly one event per rule,
   reported **boundary = 0** despite 204 base (threshold-bearing) rules,
   produced 279 phantom events on untranslated rules, and mislabelled generic
   arithmetic as `rounding`. Run 3's model fires zero-or-many events, **only on
   translated rules** (zero phantom events), requires a literal `ROUNDED` for a
   `rounding` tag, mandates boundary detection (**11 boundary events** here),
   and forbids citing a `PIC ... VALUE` line or paragraph label as evidence.

**Do Run 3's expressibility numbers track Run 2's?** No — and the gap is a
*selection* effect, not a methodology gain. Run 3's 86.4% base rate vs Run 2's
39.2% reflects that Run 3 deliberately sampled **threshold/eligibility-rich
business repos** (CardDemo, BankDemo, payroll, tax, banking), which are
prose-expressible decisions, while Run 2 swept the whole corpus including the
string-parsing, collation, and substring-heavy programs that drove its large
`pack-needed` count. Run 3 is a shape check on a favourable slice, **not** a
corpus-wide expressibility rate. A full-corpus Run 3 would be expected to land
much closer to Run 2's ~39% base.

## 4. Comparability caveats

- **Different corpora / selection pressure.** Run 1 = 3 small curated repos;
  Run 2 = full 2024 X-COBOL; Run 3 = a business-leaning *pilot subset* of the
  same 2024 corpus. The expressibility percentages are **not** drawn from the
  same population and must not be compared as if they were.
- **Different fidelity-classifier generations.** Run 1 used the original
  classifier (not re-derived for this comparison); Run 2's classifier was
  broken (boundary=0, phantom events); Run 3 uses the corrected model. The
  fidelity rows above are therefore **not the same classifier across columns** —
  most starkly, Run 2's boundary=0 is an instrument failure, not a finding.
- **Pilot scope.** Run 3's counts come from 22 rules. Treat its percentages as
  directional, not definitive. Scaling Run 3 to all 168 repos is a separate,
  gated decision.
- **Open-source, not production.** All three runs draw on public GitHub COBOL,
  not production mainframe code, and no human COBOL auditor reviewed the
  translations.

# COBOL → Liminate — Expressibility & Fidelity, Run 3

**Run 3 supersedes Run 2** as the authoritative result. Run 2 is retained as a record of a run whose corpus provenance could not be verified and whose fidelity classifier was broken (one event per rule, boundary=0 despite 204 threshold rules, 279 phantom events, generic arithmetic mislabelled as rounding). Run 3 pins corpus identity and rebuilds the fidelity model.

## 1. Run header

| Field | Value |
|---|---|
| Date | 2026-06-06 |
| Interpreter | `liminate 0.14.1` |
| Dataset | X-COBOL: A Dataset of COBOL Repositories |
| Release | **2024** |
| Zenodo record | **14269462** |
| DOI | **10.5281/zenodo.14269462** |
| COBOL files | **5,195** across **168** repos |
| Corpus fingerprint (sha256) | `ef1c12875dd0bdffa169ccc4cb3143d58090288c7138ae621c7684aeb09304b5` |
| Execution mode | **Scoped pilot** — business/finance-leaning repos; full-corpus scaling is a separate decision |
| Business-leaning repos scanned | 13 |
| Repos read in depth | 6 (carddemo, BankDemo, tax_extension, crud-payroll, taxe-fonciere, UnizarBank) |
| Rules attempted | 22 |
| Duplicates collapsed | 0 |

Identity basis: the stale 2023 `zenodo_record.json` (record 7968845, which described 84 repos / 1255 files) was removed by the maintainer after the §2 gate flagged the mismatch; the maintainer confirmed handling the 2024 upload. On-disk corroboration is internally consistent — 168 repos in both `final_repo_statistics.csv` and `repo_code_statistics.csv`, 5,195 `.cbl/.cob/.cobol` files, and a `COBOL_Files/` directory dated Dec 2024.

## 2. Expressibility

| Class | Count | Share |
|---|---:|---:|
| base | 19 | 86.4% |
| pack-needed | 3 | 13.6% |
| untranslatable | 0 | 0.0% |
| **total** | **22** | 100% |

## 3. Pack-demand summary (ranked)

| Pack label (controlled vocabulary) | Rules |
|---|---:|
| `date-arithmetic` | 2 |
| `exponentiation` | 1 |

Additionally, two `base` rules (R0012, R0021) carry a `rounding` fidelity event and represent latent demand for a **currency-rounding / decimal-scale** pack: they are expressible as arithmetic but cannot reproduce COBOL's `ROUNDED` half-up step.

## 4. Fidelity-risk summary

Corrected model: events fire **only on translated rules**; a rule may carry **zero or many** events; `boundary` requires an inclusive `>=`/`<=`/`THRU` rendered through a strict operator; `rounding` requires a literal `ROUNDED` keyword; every event cites the **actual condition/computation line** (never a `PIC ... VALUE` declaration or paragraph label).

| Kind | Count |
|---|---:|
| boundary | 11 |
| none | 6 |
| precedence | 4 |
| sign | 3 |
| rounding | 2 |
| **total events** | **26** |

**Boundary count = 11** (Run 2 reported 0 — a build failure that Run 3's mandatory boundary detector eliminates).

### Every boundary / rounding / sign event (COBOL → Liminate)

| Rule | Kind | COBOL | Liminate |
|---|---|---|---|
| R0008 | boundary | `WHEN (FS-SALBR > 0) AND (FS-SALBR <= 1556,94)` | `permit gross-salary is below 1556.95` |
| R0008 | boundary | `WHEN (FS-SALBR > 1556,94) AND (FS-SALBR <= 2594,92)` | `permit gross-salary is below 2594.93` |
| R0008 | boundary | `WHEN (FS-SALBR > 2594,92) AND (FS-SALBR <= 5189,82)` | `permit gross-salary is below 5189.83` |
| R0010 | boundary | `WHEN FS-FILHOS > 0 AND FS-SALBA <= 806,80` | `permit base-salary is below 806.81` |
| R0010 | boundary | `WHEN FS-SALBA > 806,81 AND FS-SALBA <= 1212,64 AND` | `permit base-salary is below 1212.65` |
| R0001 | boundary | `IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL` | `forbid temp-balance is above credit-limit` |
| R0003 | boundary | `IF DALYTRAN-AMT >= 0` | `permit transaction-amount is above -0.01` |
| R0003 | sign | `IF DALYTRAN-AMT >= 0` | `permit transaction-amount is above -0.01 / permit transaction-amount is below 0` |
| R0007 | boundary | `IF ACCT-CURR-BAL <= ZEROS AND` | `forbid account-balance is below 0.01` |
| R0021 | rounding | `COMPUTE COTISB-COTICOM     ROUNDED =` | `remember a value called municipal-tax with municipal-base multiplied by municipal-rate divided by 100` |
| R0011 | boundary | `IF CUR-REC-KEY >= PREV-REC-KEY` | `forbid current-key is below previous-key` |
| R0012 | rounding | `COMPUTE PREV-ADJ-BASE ROUNDED =` | `remember a value called prior-adjusted-base with prior-base multiplied by prior-multiplier` |
| R0013 | sign | `IF PREV-ADJ-BASE < 0` | `permit prior-adjusted-base is below 0` |
| R0019 | sign | `IF WS-XFER-ACCT-FROM-BAL-N IS LESS THAN ZERO` | `forbid from-balance is below 0` |
| R0014 | boundary | `IF WS-CALC-WORK-PERC-N IS NOT GREATER THAN ZERO` | `require interest-rate is above 0` |
| R0015 | boundary | `IF WS-CALC-WORK-PERC-N IS NOT LESS THAN 100.000` | `require interest-rate is below 100` |

(16 boundary/rounding/sign events total; all shown.)

## 5. Verb frequency

| Verb | Rules using it |
|---|---:|
| `remember` | 19 |
| `forbid` | 8 |
| `permit` | 5 |
| `require` | 2 |

## 6. Findings

**F1 (expressibility).** In a business/finance-leaning slice of X-COBOL, **19 of 22** isolable rules (86.4%) translate into base Liminate and are accepted by the interpreter. The rules that resist the base vocabulary are not vague business logic — they are **mechanical**: date-string ordering and exponentiation. Where COBOL encodes a *decision*, prose-as-syntax expresses it; where COBOL encodes *machine arithmetic*, a pack is needed.

**F2 (fidelity — boundaries are the dominant translation risk).** Of 26 fidelity events, **11 are boundary conversions** — inclusive COBOL comparisons (`>=`, `<=`, `NOT GREATER/LESS THAN`) re-expressed through Liminate's strict `is above`/`is below`. This is the single most common place a COBOL rewrite can silently shift who qualifies, and it is exactly the signal Run 2's classifier missed entirely (it reported zero).

**F3 (fidelity — rounding is rare and must be earned).** Only **2** events are `rounding`, and each cites a line containing the literal `ROUNDED` keyword. Generic decimal arithmetic without `ROUNDED` (e.g. CardDemo's interest `COMPUTE` and balance `COMPUTE`) is tagged `none`, not `rounding`. The corrected model refuses to inflate currency risk the way Run 2 did.

## 7. Honesty boundary

- This is **large but open-source GitHub COBOL**, not production bank-mainframe code. Selection here is further narrowed to a **business-leaning pilot**, which over-samples threshold/eligibility logic relative to the full corpus.
- One interpreter version (`0.14.1`); no human COBOL auditor reviewed the translations; dedup is heuristic (none triggered in this pilot).
- `base` acceptance means *the interpreter accepts the rule*, not that the Liminate rule is a byte-for-byte behavioural twin of the COBOL — the fidelity events are precisely the catalogue of where they may differ.
- The pilot is **not** a corpus-wide expressibility rate. It is a shape check; scaling to all 168 repos is a separate, gated decision.


# Inscript Programming Language — v2a Dogfooding Gap Inventory

**Diagnostic snapshot — what v2a unlocked, what it didn't, and what new gaps surfaced at scale**

**Status:** LOGGED — DIAGNOSTIC SNAPSHOT
**Date:** May 12, 2026
**Author:** Rob Thomas / R. Michael Thomas
**Document type:** Gap inventory — scoped to v2a (Dogfooding Resolutions, May 12, 2026). Five focused programs run against the Möbius Paradigm per-document corpus (30 records, 462,640 words total). Each gap is categorized as **v2-patch** (fixable without spec change), **v2-design** (requires new vocabulary or semantics), or **UX** (interpreter output quality). Two gaps from the v1 dogfooding are confirmed *resolved* at scale.
**Relationship to prior documents:** Extends the v1 dogfooding inventory (`inscript_gap_inventory_2026_05_12_v1_dogfooding.md`, same date) and verifies the resolutions locked in `inscript_addendum_v2a_dogfooding_resolutions.md` (same date). Operates within the locked specification (inception checkpoint v1 + addenda v1a/v1b/v1c/v1d/v2a). Does not modify any locked decision.

---

## Programs Executed

| # | Program | Records | Probe focus | Outcome |
|---|---|---|---|---|
| 9 | `dogfood_v2a_9_multipass` | 30 | D2 at scale — four orthogonal `keep` passes + one chained narrowing, all capturing via `remember ... from keep ...` | All predictions matched. Source `docs` stayed at 30 throughout. |
| 10 | `dogfood_v2a_10_tabular` | 5 | D1 at scale — 2/3/all-field display, field-ordering, single-field regression check, duplicate-field probe | All multi-field outputs render with user's field ordering. Duplicate field silently allowed (gap U1 below). |
| 11 | `dogfood_v2a_11_inspect` | 4 | D4 at scale — `of` on valid records, plus four "disallowed position" probes (list target, mid-`and`, in `where`, in value position) | Valid uses work. All four disallowed positions error cleanly with three distinct messages. |
| 12 | `dogfood_v2a_12_compositions` | 9 | D3 dissolution — three reusable `keep` compositions called repeatedly; capture-via-`from` probe | Compositions reusable; source preserved at 9 across 5 calls. **Capture-via-`from` produces a hard error (gap D9 below).** |
| 13 | `dogfood_v2a_13_edges` | 3 | Operation-sequencing with `keep`, `keep` inside `each`, multi-field with missing field, OR condition with `keep` | Sequencing emits both outputs (note U2). `keep` inside `each` errors at parse (gap D10). Missing-field error clean. OR with `keep` works. |

---

## Confirmed Resolutions (v2a at Scale)

The two structural items from the v1 inventory (D2 and D3) are confirmed dissolved at corpus scale:

- **D2 — destructive `filter` made lists single-use.** *Resolved by `keep` (§67).* Program 9 ran four independent `keep` passes plus a chained narrowing against the 30-record corpus without rebuilding the list. Final `count the docs` returned 30 in every probe. The v1 workaround (re-typing a 30-item `and` chain before each filter) was unnecessary.
- **D3 — destructive compositions silently no-op on repeated calls.** *Dissolved as a side effect of D2.* Program 12 called three `keep`-based compositions repeatedly (5 total calls). Each call produced identical output; source `docs` stayed at 9 throughout.

The three new features (D1, D4, D6) work at scale:

- **D1 — multi-field display in `each ... show`.** Programs 9, 10, and 13 used `show A and B [and C]` over 9, 5, and 3 record lists. Field ordering follows the user's order verbatim. Single-field `show A` continues to emit bare values (no regression).
- **D4 — single-record field access via `of`.** Program 11 inspected four named records. All valid uses returned the right values; all four disallowed-position probes errored cleanly.
- **D6 — descriptor preservation.** All five programs used the descriptor `doc` (and `domain`, `class`, etc., in the v1 dogfooding traces). Every canonical line preserves the user's word. Round-trip is stable.

---

## Gap Inventory

### Category: v2-design (requires new vocabulary, semantics, or spec work)

| # | Gap | Surfaced By | Description | Design Input |
|---|---|---|---|---|
| D9 | **Composition calls can't be captured via `remember ... from <comp>`** | Program 12 final line | `remember the captured called captured from find-mobius` (where `find-mobius` is a composition wrapping `keep`) produces: *"Error: Composition calls can't be used as a value in this version."* The interpreter's `_evaluate_expression` (interpreter.py) explicitly rejects `CompositionCallNode` in value position. Result: the user can define a reusable filter composition and call it for its side effect (auto-show), **but cannot capture its result for downstream analysis** — they must instead inline the `keep` body verbatim in a `remember ... from keep ...` statement, defeating the reuse purpose. The natural workflow ("define `find-major`, use it 4 ways") collapses to "redefine the body 4 ways." This is pre-existing v1 behavior (composition return values are Q9 / inception §25) but `keep` makes it newly painful — `keep` is the most natural thing to wrap in a composition for reuse. | Lock composition return-value semantics. Two paths: (a) composition return value = the value of its last expression (matching most prose languages' intuition), or (b) explicit return marker like `give the result` or `return X`. Path (a) requires only an interpreter change and matches the spirit of `gather` and `combine`'s auto-return. Path (b) requires new vocabulary. Either way, `find-mobius` should be capturable. |
| D10 | **No way to apply `keep` (or `filter`) per-record inside `each`** | Program 13 line 2 | `each the docs keep where words is above 9000` errors at parse with "I expected a target after 'keep', but 'where' is a connective." The parser is correct — `keep` requires an explicit target name, and inside an `each` body the "current item" has no name. The user has no v2a way to express "for each record, decide whether to keep it" except by wrapping the original `keep` around the whole list, which is structurally different from per-record decision logic. Business-rules use cases regularly want per-record decisions ("for each transaction, flag it if..."). | Either (a) introduce a per-record reference (an `it` pronoun mirroring `each`'s in-where usage, but in target position), or (b) accept that per-record decisions belong in a `keep`'s `where` clause, not in an `each` body, and document that more clearly. Option (b) is the smaller change; (a) is more powerful but adds a pronoun. |
| D11 | **`of` is restricted to `show` target position** | Program 11 probes 7 and 8 | `of` works after `show <field>` but not in: `where` clauses (`keep the docs where words of doc-1 is above 5000` → parse error), value positions after `with` (`remember a copy called holder with words of doc-1` → parse error), or after other verbs (`combine the words of doc-1` — not tested but would behave similarly). A natural business-rules expression is "filter rows where field X exceeds some named baseline" — currently impossible without rebinding the baseline value first. v2a §68 explicitly scoped `of` to `show`; this gap is therefore *consistent* with the spec but recurring in practice. | Generalize `of` from a `show`-only construct to a value-position construct: `<field> of <record>` should be a valid value expression wherever a value or field reference is expected. The parser change is local; the disambiguation rule is simple (after a NAME, if next token is `of`, consume `of` + record name). |

### Category: v2-patch (interpreter-only fixes without spec change)

(No v2-patch gaps surfaced. The v2a code is functionally correct for everything it locks.)

### Category: UX (interpreter output quality, error messages, display)

| # | Gap | Surfaced By | Description | Suggested Improvement |
|---|---|---|---|---|
| U7 | **Duplicate fields in multi-field `each ... show` are silently allowed** | Program 10 final line | `each the docs show domain and class and class` produces `domain: X, class: Y, class: Y` per record — two identical "class" columns. The user almost certainly mistyped (intended `domain and class and words` or similar). v2a §69 doesn't lock either acceptance or rejection. Silent acceptance lets the typo through. | Detect repeated field names in `ShowNode.extra_fields` at parse time (or semantic-analyze time). Emit a parse warning (Outcome 2 amber would over-reach) or — more in keeping with v1c §52 (deterministic interpretation only) — emit a semantic error: *"You listed 'class' twice in this show. Did you mean another field?"* The repetition is non-actionable in v1's display model (no aggregation, no aliasing) so erroring is safe. |
| U8 | **`of` on a list-of-records doesn't suggest `each`** | Program 11 probe 5 | `show words of docs` (where `docs` is a list) produces: *"Error: 'of' needs a record. 'docs' is a list of records."* Technically correct, but the user's intent is almost always "show me each doc's words" — which is `each the docs show words`. The error doesn't suggest the iteration path. | Extend the message: *"'of' needs a single record. 'docs' is a list of records — did you mean: each the docs show words?"* This is the same kind of corrective suggestion v1d §62 added for descending ranges. |
| U9 | **Operation sequencing emits both `keep`'s auto-show and the following statement's output** | Program 13 line 1 | `keep the docs where words is above 9000 and show docs` emits 6 lines: the 3 matches from `keep` (auto-show) followed by the 3 records from `show docs`. The user might have wanted either one or the other — there's no way to silence `keep`'s auto-show short of capturing into a `remember ... from keep ...`. | Two options: (a) document this clearly (operation-sequencing means both run, both output), or (b) auto-suppress a stand-alone verb's display when followed by `and <verb>`. Option (b) is a behavior change that interacts with v1d §56 (stepwise execution); not recommended without spec work. Option (a) is sufficient — likely a doc note in v2a §67. |

---

## What Worked Well

- **Four orthogonal `keep` probes on a 30-record list without a single rebuild.** The v1 dogfooding's most-painful pattern (Program 2's 30-line `and` chain typed once per filter) was simply gone. Program 9 ran four passes + one chained narrowing + an `each ... show A and B and C` at the end, all 49 lines including data setup.
- **`remember ... from keep ...` capture is the clean idiom** for the "narrow further" workflow: `remember the major called major from keep the large where domain is equal to mobius` reads as English, captures cleanly, and leaves both source lists untouched.
- **Multi-field `each ... show` is the right answer for tabular display.** Output reads as labeled rows; field order follows user intent; the format matches what `show <record>` produces, just filtered. The dogfooding pass's `dogfood_5b` program — which was originally the program that surfaced D1 — now produces exactly what a reader wants.
- **`of` errors are immediate and clear** across all four disallowed positions probed (list target, mid-`and`, `where` clause, value position). No silent misparses.
- **D3 dissolution is structural, not coincidental.** Program 12 called three `keep`-based compositions five times total; every call produced identical output and the source list (9 records) was preserved bit-for-bit. The pattern "wrap a `keep` in a composition for reuse" works the way a non-programmer would expect.
- **The D5 better error message** (composition chaining deferred) fires correctly and gives a clear next step ("Call '<name>' on its own line").
- **Descriptor preservation at scale** is invisible — which is exactly the right outcome. Every program's canonical lines preserved `doc`, `domain`, `class`, etc. The user's voice survives the round-trip.

## Cross-Check Results

| Computation | Method A | Method B | Match? |
|---|---|---|---|
| Number of mobius docs in the 30-record corpus | `remember ... from keep where domain is equal to mobius; count` (Program 9) | Manual count from data appendix | **Yes** — both `24`. |
| Number of checkpoint docs | `remember ... from keep where class is checkpoint; count` (Program 9) | Manual count | **Yes** — both `19`. |
| Number of docs with `words` > 7000 | `remember ... from keep where words is above 7000; count` (Program 9) | Manual count | **Yes** — both `12`. |
| Mobius docs *among* the words>7000 subset | `remember the major called major from keep the large where domain is equal to mobius; count` | Manual count from the 12-doc subset | **Yes** — both `9`. |
| Source list preserved after all four keeps | `count the docs` (final) | Initial `count the docs` | **Yes** — both `30`. |

All five cross-checks held. The non-destructive contract is verified at every level: `keep` doesn't touch the source; `remember ... from keep` captures a fresh list; chaining `keep` over a captured list doesn't disturb either the captured list or the original source.

---

## Second-Pass Observations (with UX polish, May 12, 2026)

After the v1 UX polish landed (U1/U4 `--quiet` flag, U2/U3 schema-mismatch wording, U5 auto-show truncation), the five v2a dogfood programs (9–13) were re-run with `--quiet`, plus three new probes (programs 14–16) were added to stress-test the polish at v2a-realistic scales. The actuals are saved alongside the originals as `*.quiet.actual.txt`.

**Headline impact: --quiet collapses canonical noise.** Trace line counts dropped substantially:

| Program | Default trace | `--quiet` trace | Reduction |
|---|---|---|---|
| 9 (multipass) | 65 | 26 | 60% |
| 10 (tabular) | 43 | 37 | 14% |
| 11 (inspect) | 18 | 11 | 39% |
| 12 (compositions) | 51 | 37 | 27% |
| 13 (edges) | 18 | 16 | 11% |

Program 9 — the headline v2a demonstration — drops most of all because its trace is dominated by 30 record-construction canonicals. With `--quiet`, the trace reads as pure data: a sequence of counts (30, 24, 30, 19, 30, 12, 30, 9, 12, 30) showing the source preserved through every probe, followed by a labeled per-record listing of the 9 final matches.

**New scale + polish probes (programs 14–16):**

| # | Program | What it probes | Outcome |
|---|---|---|---|
| 14 | `dogfood_v2a_14_realistic` | A "report-shaped" analysis: count, single-record inspections via `of`, three named compositions, multi-stage narrowing, tabular per-record output. The kind of thing a non-programmer might actually write. | With `--quiet`, output reads as a written report. No new gaps surfaced. |
| 15 | `dogfood_v2a_15_scale` | `gather 1 to 1000`, multiple `keep` captures, threshold-boundary check (20 = full display), `combine` at scale (1+2+…+1000 = 500500). | Truncation fires correctly on `gather` auto-show (`1, 2, ..., 10, ..., 991, ..., 1000`). At exactly 20 items, full display (threshold exclusive). `combine` produces 500500. Source preserved at 1000. |
| 16 | `dogfood_v2a_16_schema_errors` | A heterogeneous list with one non-matching record (`item1` among 4 `order`s) — partial-match path. Plus two zero-match paths on homogeneous lists. | All three error messages fire correctly and immediately (no canonical noise thanks to `--quiet`). Partial path: *"'item1' in 'all' doesn't have a field called 'total'. Other items do have it."* Zero path: *"No item in 'X' has a field called 'Y'."* |

**Gap status update:**

- **D9, D10, D11** — still real, unchanged. The UX polish is orthogonal to these v2-design gaps. They remain inputs to the next spec session.
- **U7** (duplicate fields silently allowed in multi-field show) — still real. Polish doesn't address this; it's an analyzer concern.
- **U8** (`of`-on-list error doesn't suggest `each`) — still real. Could ship as a small v2.1-patch with the same UX-polish style.
- **U9** (operation-sequencing emits both outputs) — still real. With `--quiet` the noise is dramatically reduced, but the dual-output semantics are unchanged.

**No new gaps surfaced.** The polish makes the existing gaps *more* visible (because the surrounding noise is gone) but doesn't reveal any unknown unknowns. The U2/U3 named-offender wording is genuinely more helpful — surfacing the specific bad record cuts the diagnostic time on heterogeneous lists from "scan the source code" to "look at the message."

**The second pass confirms v2a + UX polish is ready as a usable working language.** The remaining gaps (D9/D10/D11 + U7/U8/U9) are now sharply specified inputs to either the next spec session or a small follow-up patch round.

---

## Resume Prompt

*We are resuming from the Inscript v2a Dogfooding Gap Inventory (May 12, 2026). v2a (May 12, 2026) locked five resolutions and deferred one (D7 multi-word strings). Two passes have been completed. **First pass** (programs 9–13): five focused programs verified each v2a resolution at scale. All five v2a features work. D2 (keep) and D3 (composition reusability) are confirmed structurally resolved — four orthogonal keeps on a 30-record list with the source preserved bit-for-bit. Three new v2-design gaps surfaced: **D9** (compositions can't be captured via `remember ... from <comp-name>`), **D10** (no per-record `keep`/`filter` inside `each`), **D11** (`of` only works in `show`'s target position). Three UX gaps: **U7** (duplicate fields silently allowed), **U8** (`of`-on-list error doesn't suggest `each`), **U9** (operation-sequencing emits both outputs). **Second pass** (programs 9–13 re-run with the v1 UX polish in `--quiet` mode, plus new programs 14–16): the polish (U1/U4 `--quiet`, U2/U3 schema-mismatch wording, U5 auto-show truncation) dramatically improves the dogfooding experience — Program 9's trace drops 60% (65→26 lines), reading as pure data rather than a parser transcript. Three new probes confirmed `--quiet` + truncation at scale (`gather 1 to 1000`, `combine` = 500500, threshold exclusive at 20) and the U2/U3 named-offender wording in practice. **No new gaps in the second pass** — but the existing six remain. Recommended next step: bundle D9 into the next spec addendum (composition return values, Q9). D10 and D11 are smaller; could wait for the next dedicated session. The three UX items are tiny — could ship as v2.1-patches whenever convenient.*

---

*END OF INSCRIPT v2a DOGFOODING GAP INVENTORY*

*May 12, 2026*

*Two v1 gaps confirmed dissolved at scale. Three new gaps surfaced.*
*All three trace back to the same place: composition is the language's reuse mechanism, but compositions don't yet return values, restrict their context (each body), or compose with each other (of in non-show positions).*
*The reuse story is the next chapter.*

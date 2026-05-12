# ADDENDUM
## Inscript Programming Language — Build Boundary
### v1d — Final Implementation Locks Before First Code

**Status:** LOCKED — EXTENDS `inscript_addendum_v1c_implementation_hardening.md`
**Date:** May 11, 2026
**Author:** Rob Thomas / R. Michael Thomas
**Document type:** Addendum — locks build-boundary implementation decisions and hostile test suite; no new vocabulary, no pipeline changes, no new deferrals
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** Extends `inscript_addendum_v1c_implementation_hardening.md` (May 11, 2026), which extends v1b (same date), which extends v1a (same date), which extends the Inception Checkpoint v1 (same date). Continues from §54. A final external review (ChatGPT, May 11, 2026) of all four prior documents plus the test suite identified ten findings. This addendum resolves the ten that require build specification locks, adds a hostile test block covering every error path in the output taxonomy (v1c §50), and states the build boundary — what v1 builds and what it does not.

---

## HOW TO READ THIS DOCUMENT

- §55–§66 continue the section numbering from v1c.
- §55–§64 each lock one implementation decision.
- §65 adds the hostile test block (test sentences 35–48).
- §66 states the build boundary — the definitive scope of the first Python build.
- After this addendum, the build specification is five documents plus the expanded test suite (48 sentences). No further pre-build specification is planned.

---

### §55 — REORDERER v1 SCOPE

**Decision: The v1 parser expects canonical word order. A narrow, table-driven reorderer handles a small set of documented permutations. All other non-canonical orderings produce an error with the canonical form suggested. LOCKED as v1 reorderer scope.**

The inception checkpoint §17 (line 306) locks slot filling as the reorderer ARCHITECTURE. §9 (line 134) gives a free-order example: `the orders filter where above 50 total is` mapping to canonical form. The architecture is locked. The v1 acceptance surface — which permutations the reorderer actually handles — is what this section specifies.

**Why canonical-first:** For text input, canonical order IS natural English. `filter the orders where total is above 50` is how a person would naturally type the sentence. The reorderer was designed primarily for tile composition (§9 line 134 context, §222), where tiles can be placed in any visual order. For text input, requiring canonical order is not punitive — it is natural. The full free-order acceptance (handling deeply scrambled input like `above 50 total is where the orders filter`) is the target state for the tile interface; the v1 text interpreter starts with canonical order and a narrow tolerance band.

**The problem with broad free-order acceptance in v1:** When multiple UNKNOWN tokens appear (e.g., `orders` and `total`), slot filling cannot distinguish target from field reference without the `where` connective as a delimiter. The structural connectives (`where`, `called`, `with`, `as`, `from`, `to`) are what make slot filling unambiguous. When they are present, most orderings resolve. When they are absent or misplaced relative to other tokens, ambiguity arises (Outcome 3, v1c §50). Building a broad reorderer before the canonical parser is stable risks solving a natural-language-ordering problem instead of building Inscript.

**v1 reorderer acceptance table:**

| Permutation | Canonical form | v1 behavior |
|---|---|---|
| Canonical order | `filter the orders where total is above 50` | Accepted (no reordering needed) |
| Article + target before verb | `the orders filter where total is above 50` | Accepted — reorderer moves article + target after verb |
| Target before verb (no article) | `orders filter where total is above 50` | Accepted — reorderer moves target after verb |
| Condition elements scrambled | `filter the orders where above 50 total is` | Rejected — error: "I couldn't parse the condition. Try: filter the orders where total is above 50" |
| Verb at end | `the orders where total is above 50 filter` | Rejected — error with canonical suggestion |
| Connectives missing | `filter orders total above 50` | Amber (Outcome 3) if ambiguous, or error if unresolvable |
| All tokens scrambled | `50 above is total where orders the filter` | Rejected — error with canonical suggestion |

The reorderer is structured as a separate preprocessing step before the parser: it receives the token list, applies the acceptance table, and either produces a canonically-ordered token list (for the parser) or produces an error/amber result (returned directly). The parser always receives canonical order.

**The architecture is not deferred.** Slot filling (§17) governs the reorderer module. The module exists in v1. Its acceptance surface is narrow. As the language matures (tile interface, broader text tolerance), the acceptance surface expands — but the architecture (slot filling with verb signatures) does not change.

---

### §56 — STEPWISE EXECUTION

**Decision: Multi-operation sequences are stepwise, not transactional. Each operation in a sequence commits independently as it succeeds. If a later operation fails, earlier side effects remain. LOCKED as v1 execution model.**

The inception checkpoint §21 (line 409) locks `and` as operation sequencing: `filter the orders and show the count`. §24 locks `filter` as in-place modification. No document specifies what happens when one operation in a sequence fails after a preceding operation has already committed a side effect.

The scenario: `filter the orders where total is above 50 and show the missingname`. The filter succeeds — `orders` is modified in-place, removing records where total ≤ 50. Then `show the missingname` fails with a semantic error (name not found). Does the filter's modification persist?

**v1 answer: yes.** The filter committed when it succeeded. The later failure does not undo it. The interpreter processes each operation sequentially and independently. There is no rollback mechanism.

This is the simplest model. It is consistent with a sequential interpreter (§16) that processes statements one at a time. It is also consistent with non-programmer intuition: "I filtered the orders, then I tried to show something that doesn't exist — the filtering already happened."

Transactional execution (rolling back all operations in a sequence if any one fails) is a v2 consideration. It requires a copy-before-modify strategy or an undo log, both of which add complexity that v1 does not need.

The error message for a mid-sequence failure includes the context: "I completed 'filter the orders where total is above 50' but then couldn't find 'missingname'. The filter has already been applied."

---

### §57 — SYMBOL NAME CASE NORMALIZATION

**Decision: All symbol table names are stored in lowercase. `Age`, `age`, and `AGE` are the same symbol. LOCKED as symbol table normalization rule.**

The inception checkpoint §22 (line 424) locks: "The lexer lowercases all input before vocabulary lookup." This means user-provided names are lowercased at the lexer level — `Age` becomes `age` before the parser or symbol table ever sees it. Original casing is lost at the lexer stage.

Making this explicit: the symbol table stores names in lowercase because that is what the lexer produces. There is no casing distinction between identifiers. `remember a number called Age with 30` and `show age` refer to the same symbol.

Display values (string literals like `red`, `active`, `portland`) are also lowercased by the lexer. This means the user cannot store a case-sensitive string. For v1, this is acceptable — the language operates at the concept layer (§10), not the formatting layer. Case-sensitive string handling is a v2 consideration.

---

### §58 — DUPLICATE NAMES OVERWRITE

**Decision: When `remember` is called with a name that already exists in the symbol table, the existing value is silently overwritten with the new value. LOCKED as v1 `remember` behavior.**

No prior document specifies this behavior.

`remember a number called age with 30` followed by `remember a number called age with 40` updates `age` to 40. The old value (30) is gone.

Rationale: `remember` is "remembering." Re-remembering updates the memory. This matches non-programmer intuition — if someone says "remember my age as 40," they expect the previous value to be replaced, not an error saying "you already told me your age."

The canonical prose rendering (v1a §33) shows what is happening: "I understand this as: remember age as 40." The user sees the overwrite before execution occurs.

**Type changes are also allowed.** `remember a number called x with 30` (x is a number) followed by `remember a list called x with red and blue` (x is now a list of strings) overwrites both the value and the type. The symbol table records the new type. This is consistent with type inference from values (§23) — the type is always determined by what is stored, not by what was previously stored.

An error-on-duplicate or warning-on-duplicate mode is a v2 consideration for stricter environments (e.g., compliance rules where accidental overwrite could be dangerous).

---

### §59 — HOMOGENEOUS LISTS ONLY

**Decision: v1 lists are homogeneous — all items must be the same type. Mixed-type lists produce a semantic error. LOCKED as v1 list type constraint.**

The inception checkpoint §23 (line 458) specifies list types as "list of numbers," "list of strings," or "list of records." Q8 (line 535) explicitly flags "collections of mixed types" as remaining open.

The resolution: `remember a list called mixed with 1 and blue` is a semantic error: "A list can't mix numbers and text. '1' is a number but 'blue' is text."

The semantic analyzer checks types during list construction:
- All NUMBER tokens → list of numbers
- All UNKNOWN tokens (classified as values) → list of strings
- All tokens referencing existing records → list of records
- Any mixture → semantic error

This prevents downstream confusion: `combine` (v1b §38, numeric only) can assume its input is a list of numbers. `filter` with field-based conditions can assume all records have the same schema (see §60). Type homogeneity is a structural guarantee, not just a preference.

Mixed-type lists are a v2 consideration alongside the broader type system (Q8).

---

### §60 — RECORD SCHEMA HOMOGENEITY FOR FIELD OPERATIONS

**Decision: Field-based operations (`filter`, `each` with field access) require every record in the target list to contain the referenced field. If any record lacks the field, the semantic analyzer produces an error before execution. LOCKED as v1 schema enforcement rule.**

The inception checkpoint §23 (line 452) says the semantic analyzer "verifies that `total` is a field on items in `orders` by checking the schema recorded in the symbol table." But the mechanism for checking schema across a list of records is unspecified.

The resolution: when the semantic analyzer encounters a field reference (e.g., `total` in `filter the orders where total is above 50`), it checks the schema of EVERY record in the target list. If any record lacks the referenced field, the operation is rejected before execution.

Error message: "Not every item in 'orders' has a field called 'total'. Check your data."

This prevents silent data loss. Without this rule, the interpreter could either skip records without the field (losing data silently) or crash mid-iteration (leaving the list in a partially-filtered state, which violates determinism). Checking before execution is the only option consistent with v1c §52 (deterministic interpretation only) and v1c §50 (semantic errors halt before execution).

---

### §61 — SINGLE-TOKEN STRING VALUES IN v1

**Decision: v1 string values are single-token bare words. Multi-word strings are not supported. LOCKED as v1 string constraint.**

The inception checkpoint §22 locks whitespace splitting: the lexer splits input on whitespace. v1c §46 locks that vocabulary words cannot be string values. The combination means v1 strings are individual words that are not in the vocabulary table and are not numbers.

Multi-word values like `in progress`, `high priority`, `Los Angeles`, or `net 30` cannot be represented in v1. Each word would be tokenized separately and classified independently by the parser.

This is a real limitation for the v1 target domains (business rules, compliance). A rule about an order with status `in progress` cannot be expressed because `in` and `progress` are separate tokens (and `in` might collide with a future connective).

**This limitation should be stated in any v1 documentation or README.** v1 supports single-word string values only. Multi-word strings require either a quoting mechanism or a multi-word token system — both are v2 considerations.

---

### §62 — DESCENDING RANGES ARE ERRORS

**Decision: `gather` requires the `from` value to be less than or equal to the `to` value. Descending ranges produce a semantic error. LOCKED as v1 `gather` range constraint.**

`gather the numbers from 10 to 1` → semantic error: "The 'from' value (10) must be less than or equal to the 'to' value (1). Try: gather the numbers from 1 to 10."

The `to` disambiguation rule (§11 line 183) confirms that range endpoints follow the pattern `from NUMBER to NUMBER` — both are literal numbers in v1. The semantic analyzer computes the range and validates the direction.

`gather the numbers from 5 to 5` produces a single-element list: [5]. Equal endpoints are allowed.

Descending ranges, step values, and non-integer ranges are v2 considerations.

---

### §63 — GATHER RANGE CAP

**Decision: `gather` enforces a maximum range size of 10,000 items. Ranges exceeding this produce a semantic error. LOCKED as v1 resource safety limit.**

`gather the numbers from 1 to 100000` → semantic error: "That range is too large. The maximum is 10,000 items."

The cap applies to the size of the resulting list (computed as `to - from + 1`), not to the values themselves. `gather the numbers from 999990 to 1000000` produces 11 items (allowed). `gather the numbers from 1 to 10001` produces 10,001 items (rejected).

Without this cap, a single `gather` statement could allocate a massive list and exhaust memory. v1 has no external data sources — `gather` and `remember` are the only ways to create data. Of the two, `gather` can produce large lists from two numbers, making it the primary resource safety concern.

The cap value (10,000) is practical for v1's target use cases (business rules on hundreds or low thousands of records) and large enough to not interfere with reasonable programs.

---

### §64 — STRUCTURED RESULT OBJECTS

**Decision: The core interpreter returns a structured result object for every statement. The interpreter never calls `input()` or `print()` directly. A thin CLI wrapper handles display and user interaction. LOCKED as interpreter interface contract.**

The interpreter processes a statement and returns a result containing:

- **status** — one of the five outcomes from v1c §50: `success`, `amber_precedence`, `amber_ambiguity`, `error_parse`, `error_semantic`
- **canonical** — the canonical prose rendering of the parsed AST (present for all outcomes except parse failure, where the AST could not be built)
- **output** — the display output produced by the statement (present only for success outcomes that produce output: `show`, auto-show, `each` with output sub-operation)
- **message** — the error or amber message (present for all non-success outcomes)
- **executed** — whether the statement was executed (true only for success; false for amber and all errors)

For amber outcomes, the CLI wrapper displays the message and prompts for confirmation. If confirmed, the wrapper calls the interpreter's `confirm()` method with the pending AST, which executes and returns a success result. If declined, no execution occurs. This two-step flow keeps the core interpreter stateless and testable.

For automated testing, the test harness processes results programmatically — checking status, canonical rendering, output, and messages without interactive prompts. Amber results can be auto-confirmed or auto-declined in test mode.

This separation is the same principle as separating the interpreter from the tile interface (§16): the interpreter is the engine; the CLI is one surface; the tile interface is another surface; all consume the same structured results.

---

### §65 — HOSTILE TEST BLOCK

The following test sentences cover error paths, edge cases, and the behaviors locked in §55–§64. They extend the test suite from 34 sentences (v1c §53) to 48 sentences.

**Sentence 35 — Name not found (semantic error)**
```
show missingname
```
⚠ Outcome 5 (semantic error): "I can't find 'missingname'. You might need to 'remember' it first."
**Tests:** Semantic error for undefined name. Output taxonomy Outcome 5.

**Sentence 36 — Filter applied to scalar (semantic error)**
```
remember a number called age with 30
filter age where each is above 5
```
⚠ Outcome 5: "I can only filter a list. 'age' is a number."
**Tests:** Type error — `filter` requires a collection, `age` is a scalar.

**Sentence 37 — Combine applied to strings (semantic error)**
```
remember a list called colors with red and blue and green
combine colors
```
⚠ Outcome 5: "I can only combine numbers. 'colors' contains text."
**Tests:** v1b §38 — `combine` is numeric-only in v1.

**Sentence 38 — Missing field on record (semantic error)**
```
remember an order called order1 with total as 75 and status as active
remember a list called orders with order1
filter the orders where missingfield is above 50
```
⚠ Outcome 5: "'orders' doesn't have a field called 'missingfield'."
**Tests:** Semantic error for field not found on record.

**Sentence 39 — Each applied to scalar (semantic error)**
```
remember a number called age with 30
each the age show
```
⚠ Outcome 5: "I can only iterate over a list. 'age' is a number."
**Tests:** Type error — `each` requires a collection.

**Sentence 40 — Descriptor contradicts value type (succeeds)**
```
remember a number called label with hello
show label
```
→ `hello`
**Tests:** v1b §36 — descriptor `number` is decorative, ignored. Type inferred from value: `hello` is a string. No error.

**Sentence 41 — Mixed-type list (semantic error)**
```
remember a list called mixed with 1 and blue
```
⚠ Outcome 5: "A list can't mix numbers and text. '1' is a number but 'blue' is text."
**Tests:** §59 — homogeneous lists only.

**Sentence 42 — Descending range (semantic error)**
```
gather the numbers from 10 to 1
```
⚠ Outcome 5: "The 'from' value (10) must be less than or equal to the 'to' value (1)."
**Tests:** §62 — descending ranges are errors.

**Sentence 43 — Range cap exceeded (semantic error)**
```
gather the numbers from 1 to 20000
```
⚠ Outcome 5: "That range is too large. The maximum is 10,000 items."
**Tests:** §63 — gather range cap.

**Sentence 44 — Duplicate name overwrite (succeeds)**
```
remember a number called age with 30
remember a number called age with 40
show age
```
→ `40`
**Tests:** §58 — duplicate names overwrite silently.

**Sentence 45 — Malformed record (parse error)**
```
remember an order called order1 with total as 75 and status
```
⚠ Outcome 4 (parse error): "I expected a value after 'status'. Try: 'status as [value]'."
**Tests:** Unfilled slot in `with...as` clause — `status` without `as [value]` leaves the field's value slot empty.

**Sentence 46 — Composition definition succeeds, call fails (semantic error at call time)**
```
remember how to show-missing: show missingname
show-missing
```
⚠ Line 1: Success (grammar valid at definition time, per §23 line 466).
⚠ Line 2: Outcome 5 (semantic error at call time): "I can't find 'missingname'."
**Tests:** §23 composition validation split — grammar at definition, names at call. Named composition call via v1b §41 parser fallback.

**Sentence 47 — Stepwise failure (filter commits, second operation fails)**
```
remember a list called nums with 1 and 2 and 3 and 4 and 5
filter nums where each is above 3 and show missingname
show nums
```
→ Line 2: filter commits (nums = [4, 5]), then `show missingname` fails. Error: "I completed 'filter nums where each is above 3' but then couldn't find 'missingname'. The filter has already been applied."
→ Line 3: `4, 5`
**Tests:** §56 — stepwise execution. In-place filter persists despite later failure in the same sequence.

**Sentence 48 — Schema mismatch in list (semantic error)**
```
remember an order called order1 with total as 75 and status as active
remember an item called item1 with price as 30 and color as red
remember a list called mixed-records with order1 and item1
filter the mixed-records where total is above 50
```
⚠ Outcome 5: "Not every item in 'mixed-records' has a field called 'total'."
**Tests:** §60 — record schema homogeneity. `item1` lacks `total`.

---

### §66 — BUILD BOUNDARY STATEMENT

The v1 build produces **a Python text interpreter that can lex, parse, semantically validate, canonicalize, and execute the 48 locked test sentences with structured result objects.**

**What v1 builds:**

| Component | Scope |
|---|---|
| **Lexer** | Case-insensitive tokenization, vocabulary lookup, `equal to` multi-word handling, number recognition, punctuation stripping, colon delimiter, blank line skipping, `an` article recognition |
| **Reorderer** | Narrow, table-driven: target-before-verb accepted, condition-scrambling rejected, canonical suggestion on rejection |
| **Parser** | Canonical-order slot filling, all seven disambiguation rules (v1b §44), recursive descent for `each` and `from`-with-verb-phrase, named composition definition parsing |
| **Semantic analyzer** | Symbol table with types, field resolution against record schemas, schema homogeneity check, type checking, range validation (direction + cap), list homogeneity check, reserved word and vocabulary-word-in-value enforcement, composition grammar validation |
| **Interpreter** | Sequential execution, auto-show, in-place `filter`, inline `gather` naming and display, copy semantics, `combine` as numeric sum, `each` with iterator context, overwrite on duplicate names, stepwise operation sequences |
| **Canonical renderer** | AST-to-prose rendering for every successful parse |
| **Result interface** | Structured result objects (status, canonical, output, message, executed), no direct I/O |
| **CLI wrapper** | Thin layer handling display, amber confirmation prompts, file input |

**What v1 does NOT build:**

- Tile interface (Branch C)
- Proposal engine / authorize-don't-author interaction (Branch E)
- Narratia Core integration (Branch E)
- Domain packs
- Event-driven execution / `when`/`unless` (Branch F, v2)
- `transform`/`choose`/`compare` verbs (v2)
- Symbolic syntax surface (Surface 3, §12)
- External data sources
- Multi-word strings / quoting
- Composition parameters / `from` chaining
- Scope isolation
- Mixed-type lists
- Descending ranges
- Any deployment beyond terminal / script file execution

The first milestone is not "Inscript as a human-centered programming environment." The first milestone is: **a deterministic Python text interpreter that passes 48 test sentences — 34 validating correct behavior, 14 validating correct failure behavior — returning structured results for every statement.**

---

## WHAT IS LOCKED

This addendum locks:

- **Reorderer v1 scope.** Canonical-order parser with narrow table-driven reorderer (target-before-verb accepted, condition-scrambling rejected). Slot-filling architecture (§17) governs; acceptance surface starts narrow. (§55)
- **Stepwise execution.** Multi-operation sequences commit independently. No rollback on later failure. (§56)
- **Symbol names are lowercase.** Consequence of lexer case normalization (§22). Explicit for symbol table. (§57)
- **Duplicate names overwrite.** `remember` with an existing name replaces the value and type. (§58)
- **Homogeneous lists only.** Mixed-type lists produce semantic error. (§59)
- **Record schema homogeneity.** Field operations require every record in the list to contain the referenced field. Semantic error before execution if not. (§60)
- **Single-token strings.** Multi-word string values not supported in v1. (§61)
- **Descending ranges are errors.** `from` must be ≤ `to`. (§62)
- **Gather range cap.** Maximum 10,000 items. (§63)
- **Structured result objects.** Interpreter returns data, never calls `input()`/`print()`. CLI wrapper handles I/O. (§64)
- **Hostile test block.** 14 negative test sentences (35–48) covering every error path. (§65)
- **Build boundary.** What v1 builds and does not build. (§66)

---

## RESUME PROMPT (Inscript Programming Language v1d)

*We are resuming from the Inscript Programming Language Build Boundary Addendum v1d (May 11, 2026), which extends v1c Implementation Hardening, v1b Design Resolutions, v1a Pre-Build, and the Inception Checkpoint v1 (all same date). v1d is the final pre-build addendum. It resolves ten review findings and adds two final build locks — the hostile test block and the build boundary statement. The ten review findings: (1) Reorderer v1 scope — canonical-order parser first, narrow table-driven reorderer for target-before-verb permutations, all other orderings rejected with canonical suggestion; (2) Stepwise execution — multi-operation sequences commit independently, no rollback; (3) Symbol names stored lowercase; (4) Duplicate `remember` names overwrite silently; (5) Homogeneous lists only — mixed types = semantic error; (6) Record schema homogeneity — field operations require all records to have the field; (7) Single-token strings only in v1; (8) Descending ranges are errors; (9) Gather range cap = 10,000 items; (10) Structured result objects — interpreter returns data, CLI wrapper handles I/O. The two build locks: hostile test block (14 negative test sentences, 35–48) and build boundary statement. Build specification is five documents: inception checkpoint v1, addenda v1a/v1b/v1c/v1d, plus 48-sentence test suite. Build produces a Python text interpreter with lexer, narrow reorderer, canonical-order parser, semantic analyzer, interpreter, canonical renderer, result interface, and CLI wrapper. Rob is architect; Claude is builder. First milestone: pass all 48 test sentences with structured result objects.*

---

## PROVENANCE NOTE

This document was verified against:

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026):
  - §17 reorderer architecture (slot filling) locked at line 306. Free-order example at §9 (line 134): `the orders filter where above 50 total is`. Ambiguity handling (line 329): "the reorderer does not guess."
  - §21 operation sequencing `and` (line 409): "After a complete verb phrase, next word is a verb." Failure behavior NOT specified — confirmed gap.
  - §22 case insensitivity (line 424): "The lexer lowercases all input." Symbol table name normalization NOT explicitly stated — confirmed gap.
  - §23 symbol table types (line 458): "list of numbers," "list of strings," "list of records" — homogeneous implied but not stated. Q8 (line 535): "collections of mixed types" flagged as remaining open.
  - §23 schema checking (line 452): semantic analyzer checks field "on items in `orders`" — per-record checking NOT specified.
  - §11 `to` disambiguation (line 183): "after `from` + number = range" — confirms gather endpoints are literal numbers.
  - §24 `filter` in-place (line 478), copy semantics (line 486), auto-show (line 472). All confirmed.
  - Duplicate name behavior: NOT specified in any section. Confirmed gap.
  - Range limits: NOT specified. Confirmed gap.
  - Descending range behavior: NOT specified. Confirmed gap.
- **`inscript_addendum_v1a_pre_build.md`** (May 11, 2026):
  - §33 canonical prose rendering. §29 reserved words (28, updated to 29 in v1c §47). §30 mixed-precedence amber. All confirmed.
- **`inscript_addendum_v1b_design_resolutions.md`** (May 11, 2026):
  - §36 prose descriptors decorative. §37 `each` dual role. §38 `combine` numeric-only. §41 composition call fallback. §44 seven disambiguation rules. All confirmed.
- **`inscript_addendum_v1c_implementation_hardening.md`** (May 11, 2026):
  - §46 vocabulary words in value positions. §47 `an` article (29 reserved words). §48 blank lines skipped. §49 iterator context. §50 five-outcome taxonomy. §51 parser lookahead capability. §52 deterministic interpretation only. All confirmed.
- **`inscript_v1_thirty_sentences.md`** (May 11, 2026): Original 30 sentences + v1c additions (31–34) confirmed. Hostile test sentences 35–48 extend coverage to error paths.
- **ChatGPT external review** (May 11, 2026): Ten findings. All ten dispositioned. Nine locked (§55–§63, §64). One (positioning/v1 naming) logged, not locked — Q1/Q2 territory.
- **Filename:** `inscript_addendum_v1d_build_boundary.md` — domain `inscript` (provisional, pre-vault), class `addendum` (per skill table), version `v1d` (fourth addendum to v1, following v1a/v1b/v1c), subtitle `build_boundary`. Verified against naming grammar in rmt-working-documents skill.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE BUILD BOUNDARY ADDENDUM v1d*

*May 11, 2026*

*Two external reviewers. Fifteen findings across them. Zero left unaddressed.*
*Five documents. Forty-eight test sentences. Twenty-nine reserved words.*
*Seven disambiguation rules. Five outcome categories. One invariant: the prose IS the program.*
*The specification is complete.*
*Build less than the documents inspire you to build.*
*Build exactly what they say.*

# ADDENDUM
## Inscript Programming Language — Design Resolutions
### v1b — Locking Decisions Surfaced by the Thirty Sentences

**Status:** LOCKED — EXTENDS `inscript_addendum_v1a_pre_build.md`
**Date:** May 11, 2026
**Author:** Rob Thomas / R. Michael Thomas
**Document type:** Addendum — locks design decisions surfaced by the thirty example sentences; no new architecture
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** Extends `inscript_addendum_v1a_pre_build.md` (May 11, 2026), which extends `inscript_inception_checkpoint_v1.md` (May 11, 2026). Continues from §35 (Pre-Build Plan). The thirty example sentences (`inscript_v1_thirty_sentences.md`) surfaced eight design questions (DQ1–DQ8) that require resolution before the lexer, parser, and interpreter can be built. All eight were analyzed against the inception checkpoint's locked decisions, presented with recommendations, and approved by the architect. This addendum formalizes those approvals as locked decisions. No vocabulary changes. No pipeline changes. No new deferrals.

---

## HOW TO READ THIS DOCUMENT

- §36–§43 each lock one design question resolution.
- §44 summarizes the complete parser disambiguation ruleset — the accumulated context-dependent rules from the inception checkpoint and both addenda, collected in one place for build reference.
- §45 confirms the build specification is complete and enumerates the three documents that constitute it.

---

### §36 — PROSE DESCRIPTORS ARE DECORATIVE (DQ1)

**Decision: Unknown words between an article and the `called` connective are ignored by the parser as decorative prose. They carry no semantic weight. LOCKED as parser rule.**

In `remember a number called age with 30`, the word `number` is not in the vocabulary table — the lexer tags it as UNKNOWN. The parser, processing a `remember` statement, encounters the sequence: article → unknown → `called`. The unknown word occupies a position between two structural elements but does not fill any slot in the `remember` verb signature (value + name, per §17).

The inception checkpoint locks type inference from values, not from annotations (§23 line 458): "`75` is a number, `active` is a string. No explicit type annotations required." Descriptors like `number`, `list`, `order`, `word`, `value` — all of which appear in the thirty sentences — are prose that makes the sentence read as natural English. The parser ignores them.

Consequence: `remember a called age with 30`, `remember a number called age with 30`, and `remember a thing called age with 30` all produce the same AST and the same symbol table entry.

No descriptor-vs-type validation in v1. If a user writes `remember a number called age with hello`, the type is inferred from the value `hello` (string), not from the descriptor `number`. No error is produced for the mismatch. Descriptor validation is a v2 consideration.

---

### §37 — `each` DUAL ROLE: VERB AND PRONOUN (DQ2)

**Decision: The parser disambiguates `each` by clause context. Inside a `where` clause, `each` is a self-reference pronoun meaning "the current item being tested." In verb position, `each` is the iteration verb with signature collection + action. LOCKED as `each` disambiguation rule.**

The inception checkpoint uses `each` in both roles without naming the disambiguation:
- **Verb role:** §17 (line 323) signature `each` → collection + action. §24 (line 476): "`each` produces output if its sub-operation produces output." §21/resume prompt: "`each` wraps sub-operations via recursive descent."
- **Pronoun role:** §11 example (line 206): `filter the numbers where each is above 50`. §23 (line 460): `filter the numbers where each is above hello` → type error. §24 (line 480): `filter the numbers where each is above 3`.

The structural necessity: for lists of records, field names serve as the condition reference (`where total is above 50`). For flat lists (lists of numbers, lists of strings), there is no field name. `each` is the only v1 mechanism for flat-list self-reference. Without it, `filter the numbers where [???] is above 5` has no valid syntax.

The disambiguation rule: if parser state is inside a `where` clause, `each` is reclassified from verb to self-reference pronoun and fills the field-reference slot. Otherwise, `each` is the iteration verb. Parser state alone resolves it — no lookahead needed.

This follows the same pattern as `and`/`or` (four meanings by parser state + lookahead, §21) and `is` (two meanings by lookahead, §21). `each` is the third vocabulary word with context-dependent meaning, and the simplest — one check, one bit of parser state.

---

### §38 — `combine` OPERATES ON NUMBERS ONLY IN v1 (DQ3)

**Decision: In v1, `combine` operates on lists of numbers and produces their sum. Applying `combine` to a list of strings or records produces a type error. LOCKED as v1 `combine` semantics.**

The `combine` verb signature (§17 line 320) is `targets` — deliberately general. The only example in the inception checkpoint (§11 line 208: `remember the total called sum from combine the numbers`) is numeric.

For v1, `combine` is unambiguous: it sums numbers. The type error message: "I can only combine numbers right now. [name] contains [type]."

String concatenation and record merging are v2 considerations that require additional grammar to specify the operation (separator for strings, merge strategy for records). Keeping `combine` numeric-only in v1 avoids under-specification — the same failure mode that deferred `transform`, `choose`, and `compare` (§21 line 401).

---

### §39 — `combine` DOES NOT MODIFY THE SOURCE (DQ4)

**Decision: `combine` returns a new value (the sum) without modifying the source collection. LOCKED as v1 `combine` behavior.**

The inception checkpoint locks only `filter` as in-place modification (§24 line 478). §24 (line 486) locks copy semantics for all data operations. `combine` produces a scalar from a collection — there is no meaningful "in-place" version of this operation (the collection cannot become its own sum).

After `combine the numbers`, `numbers` is unchanged. The sum is:
- Auto-shown if `combine` is a standalone expression (§24 auto-show rule).
- Captured and named if used in `remember the result called total from combine the numbers`.

This is confirmed by the thirty sentences: sentence 18 (`combine the numbers` → 40) and sentence 19 (`remember the result called total from combine the numbers`) both operate on the same unchanged list.

---

### §40 — `gather` BOTH STORES AND AUTO-SHOWS (DQ5)

**Decision: `gather` unconditionally stores its result in the symbol table AND displays the result. LOCKED as v1 `gather` behavior, superseding the parenthetical in §24.**

The inception checkpoint contains a contradiction between two locked decisions:
- §24 (line 476): auto-show applies to `gather` "(when not creating a named collection)."
- §24 (line 482): "`gather` creates named collections inline. LOCKED as v1 `gather` semantics." The name is parsed from the noun after the article.

If `gather` always creates a named collection, and auto-show only fires when it doesn't, `gather` never auto-shows. This contradicts the non-programmer expectation: `gather the numbers from 1 to 10` should show the numbers.

The resolution: `gather` is the one verb where both the side effect (storing) and the display (showing) happen unconditionally. The parenthetical "(when not creating a named collection)" in §24 was written before the inline-naming decision was finalized. This addendum supersedes the parenthetical — `gather` always names AND always shows.

---

### §41 — NAMED COMPOSITION CALLS IN v1 (DQ6)

**Decision: Named composition calls in v1 are standalone statements — the composition name on its own line, executing its stored body against the current symbol table. The `from` chaining syntax is deferred to v2 along with composition parameters. LOCKED as v1 composition call syntax.**

The parser's Step 1 (§17 line 312) is "find the verb." In a standalone `find-big-orders`, there is no vocabulary verb. The inception checkpoint shows composition calls (§19 line 380, §23 line 468) but never specifies how the parser handles the absence of a vocabulary verb.

The resolution: the parser's verb-finding step gets a fallback. If no vocabulary verb is found in the token stream, the parser checks whether the first unknown token is a known named composition in the symbol table. If so, it retrieves the stored verb phrase (which contains a vocabulary verb from the definition body) and parses that. The composition name effectively becomes a user-defined verb.

**Scoping clarification:** The §19 example `find-big-orders from find-loyal-customers` (line 380) demonstrates composition chaining — the output of one composition as input to another. This is parameter passing, which Q9 (line 536) explicitly leaves open ("whether compositions can accept parameters") and the v2 deferral table (line 518) explicitly defers ("Named composition parameters — compositions that accept arguments at call time"). The `from` chaining syntax is therefore a v2 feature. It demonstrates what the language will do, not what v1 executes.

For v1, a composition call is: `find-big-orders` — standalone name, no `from`, no parameters. The call-time name resolution locked in §23 (line 464) applies: the stored body executes with names resolved against the live symbol table.

---

### §42 — DISPLAY FORMAT (DQ7)

**Decision: v1 display format for `show` and auto-show output is specified as follows. LOCKED as v1 display format.**

| Type | Format | Example |
|---|---|---|
| Number | As-is | `30`, `3.14` |
| String | As-is, no quotes | `active`, `portland` |
| List of numbers | Comma-separated | `1, 2, 3, 4, 5` |
| List of strings | Comma-separated | `red, blue, green` |
| Record | Field: value pairs, comma-separated | `total: 75, status: active` |
| List of records | One record per line | Line 1: `total: 75, status: active`; Line 2: `total: 30, status: active` |
| `each...show [field]` | One value per line | Line 1: `75`; Line 2: `30` |

These are v1 defaults. A formatting system (alignment, custom separators, headers for tabular display) is a v2 consideration.

---

### §43 — `from` CONTEXT-DEPENDENT DISAMBIGUATION (DQ8)

**Decision: The `from` connective has two roles in v1, disambiguated by the active verb and the next token. LOCKED as `from` disambiguation rule.**

The inception checkpoint explicitly addresses `to`'s dual role (§11 line 183) and `is`'s dual role (§21). `from` has multiple roles demonstrated in examples (lines 205, 208, 380, 468, 474) but its disambiguation is never named as a parser rule.

**v1 roles:**

| Context | Meaning | Disambiguation |
|---|---|---|
| In `gather`, next token is a number | Range start: `gather the numbers from 1 to 10` | Active verb = `gather`, next token = NUMBER |
| In `remember`, next token is a verb | Result capture: `remember ... from combine the numbers` | Active verb = `remember`, next token = VERB → recursive descent to parse sub-expression |
| In `remember`, next token is a name | Simple reference: `remember the copy called backup from the-data` | Active verb = `remember`, next token = UNKNOWN (name) |

**Deferred to v2:** `from` as data source or composition chaining (`find-big-orders from find-loyal-customers`, `find-big-orders from the shop`). Deferred along with composition parameters (Q9, §25 line 518).

The result-capture role (active verb = `remember`, next token = verb) triggers recursive descent — the parser parses a complete verb phrase after `from` and uses its return value as `remember`'s value. This is the same recursive descent mechanism locked for `each` in §21 (line 500): "`each` wraps sub-operations via recursive descent."

---

### §44 — COMPLETE PARSER DISAMBIGUATION RULESET

For build reference: the accumulated context-dependent disambiguation rules across all three documents. Every vocabulary word with more than one meaning, and the rule that resolves it.

| Word | Meanings | Rule | Source |
|---|---|---|---|
| `and` | (1) List construction, (2) Compound condition, (3) Operation sequencing, (4) Record field continuation | Parser state + lookahead. Four context rules. | Inception §21 |
| `or` | (1) List construction, (2) Compound condition, (3) Operation sequencing, (4) Record field continuation | Same four rules as `and`. | Inception §21 |
| `is` | (1) Comparison introducer (`is above`), (2) Equality operator (`is active`) | Lookahead: next token is known operator → introducer; next token is value/name → equality. | Inception §21 |
| `not` | Operator modifier producing distinct semantics | Always modifies the following operator. `not above` = ≤, `not below` = ≥, `not equal to` = ≠. | Inception §21 |
| `to` | (1) Range endpoint in `gather`, (2) Part of `equal to` operator | After `from` + number → range. After `equal` → multi-word operator. | Inception §11 |
| `from` | (1) Range start in `gather`, (2) Result capture in `remember` (verb phrase), (3) Simple reference in `remember` (name) | Active verb + next-token lookahead. | This addendum §43 |
| `each` | (1) Iteration verb, (2) Self-reference pronoun in `where` | Parser state: inside `where` → pronoun; verb position → verb. | This addendum §37 |
| Mixed `and`/`or` | Precedence ambiguity in compound conditions | `and` binds tighter than `or`. Mixed chains trigger Amber Light for user confirmation. | Inception §21 + v1a §30 |

Seven words with context-dependent meanings, all resolved deterministically by parser state and/or lookahead. No probabilistic disambiguation. No NLU. The bounded vocabulary makes this possible.

---

### §45 — BUILD SPECIFICATION COMPLETE

The three documents that constitute the Inscript Programming Language v1 build specification:

1. **`inscript_inception_checkpoint_v1.md`** — The language design. Vocabulary, pipeline, verb signatures, reorderer architecture, graduation model, vocabulary scaling, interpreter behaviors. All architectural decisions.
2. **`inscript_addendum_v1a_pre_build.md`** — Pre-build gap closures. Reserved word exclusion, mixed-precedence Amber Light, AST-state-filtered tray, authorization as compositional act, canonical prose rendering. Stress test disposition. Build plan and acceptance criteria.
3. **`inscript_addendum_v1b_design_resolutions.md`** — Design resolutions. Eight decisions surfaced by the thirty sentences: prose descriptors, `each` dual role, `combine` semantics, `combine` non-destructive, `gather` auto-show, composition call syntax, display format, `from` disambiguation. Complete parser disambiguation ruleset.

Supporting artifact: **`inscript_v1_thirty_sentences.md`** — The test specification. Thirty-one sentences organized as five programs plus standalone tests. Expected behavior at each stage. Every verb, operator, connective, and disambiguation rule exercised.

The build sequence (inception §16, v1a §35): thirty sentences (complete) → lexer → parser → semantic analyzer → interpreter. Each stage tested against all thirty-one sentences before the next stage begins.

---

## WHAT IS LOCKED

This addendum locks:

- **Prose descriptors are decorative.** Unknown words between article and `called` are ignored by the parser. No type validation against descriptors in v1. (§36)
- **`each` dual role.** Inside a `where` clause → self-reference pronoun. In verb position → iteration verb. Disambiguated by parser state alone. (§37)
- **`combine` is numeric-only in v1.** Produces the sum of a list of numbers. Type error on strings or records. (§38)
- **`combine` does not modify the source.** Returns a new value; source collection unchanged. (§39)
- **`gather` both stores and auto-shows.** Supersedes the §24 parenthetical. Always names, always displays. (§40)
- **v1 composition calls are standalone names.** No `from` parameter passing, no chaining. Parser falls back to symbol table lookup when no vocabulary verb is found. `from` chaining deferred to v2 with composition parameters. (§41)
- **v1 display format.** Numbers as-is, strings without quotes, lists comma-separated, records as field: value pairs, lists of records one per line. (§42)
- **`from` disambiguation.** Two v1 roles: range start in `gather` (next token = number), result capture in `remember` (next token = verb → recursive descent, next token = name → simple reference). Composition chaining deferred to v2. (§43)
- **Complete parser disambiguation ruleset.** Seven words with context-dependent meanings, all resolved deterministically. Collected in §44 for build reference. (§44)

---

## RESUME PROMPT (Inscript Programming Language v1b)

*We are resuming from the Inscript Programming Language Design Resolutions Addendum v1b (May 11, 2026), which extends v1a Pre-Build (same date), which extends the Inception Checkpoint v1 (same date). v1b locks eight design decisions surfaced by the thirty example sentences: (1) Prose descriptors between article and `called` are decorative — parser ignores them; (2) `each` has two roles — iteration verb (verb position) and self-reference pronoun (inside `where` clause), disambiguated by parser state; (3) `combine` is numeric-only in v1 (sum), type error on strings/records; (4) `combine` does not modify the source collection; (5) `gather` both stores and auto-shows, superseding the §24 parenthetical; (6) v1 composition calls are standalone names — parser falls back to symbol table when no vocabulary verb found, `from` chaining deferred to v2 with composition parameters (Q9); (7) v1 display format locked (numbers as-is, strings no quotes, lists comma-separated, records field: value, lists of records one per line); (8) `from` has two v1 roles — range start in `gather` (next=number) and result capture in `remember` (next=verb → recursive descent, next=name → reference), composition chaining deferred to v2. Complete parser disambiguation ruleset: seven words with context-dependent meanings (`and`, `or`, `is`, `not`, `to`, `from`, `each`), all resolved deterministically by parser state and/or lookahead. Build specification is three documents: inception checkpoint v1, addendum v1a, addendum v1b, plus the thirty sentences test spec. Build sequence: lexer → parser → semantic analyzer → interpreter. Rob is architect; Claude is builder.*

---

## PROVENANCE NOTE

This document was verified against:

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026):
  - `each` verb signature confirmed at §17 (line 323): `each` → collection + action.
  - `each` as pronoun in `where` clause confirmed at §11 example (line 206): `filter the numbers where each is above 50`. Confirmed at §23 semantic analysis (line 460). Confirmed at §24 interpreter (line 480).
  - `each` wraps sub-operations via recursive descent confirmed at §21/resume prompt (line 500).
  - `combine` signature confirmed at §17 (line 320): `combine` → targets.
  - `combine` numeric example confirmed at §11 (line 208): `remember the total called sum from combine the numbers`.
  - `filter` in-place modification confirmed at §24 (line 478). Copy semantics for all data confirmed at §24 (line 486).
  - `gather` auto-show parenthetical confirmed at §24 (line 476). `gather` inline naming confirmed at §24 (line 482).
  - Type inference from values confirmed at §23 (line 458).
  - `to` dual role confirmed at §11 (line 183).
  - `is` dual role confirmed at §21 (line 414).
  - `and`/`or` four context rules confirmed at §21 (lines 403–411).
  - `not` operator semantics confirmed at §21 (line 416).
  - `from` range usage confirmed at §11 example (line 205).
  - `from` result capture confirmed at §11 example (line 208) and §24 (line 474).
  - `from` composition chaining confirmed at §19 (line 380) and §23 (line 468).
  - Composition parameters deferred to v2 confirmed at §25 (line 518) and Q9 (line 536).
  - Named composition call-time resolution confirmed at §23 (line 464).
  - Parser verb-finding Step 1 confirmed at §17 (line 312).
- **`inscript_addendum_v1a_pre_build.md`** (May 11, 2026):
  - Reserved word list (28 words) confirmed at §29.
  - Mixed-precedence Amber Light confirmed at §30.
  - Build plan and acceptance criteria confirmed at §35.
- **`inscript_v1_thirty_sentences.md`** (May 11, 2026): Design questions DQ1–DQ8 and their sentence references confirmed.
- **`mobius_paradigm_checkpoint_v7_5g_inscript_resolution.md`**: "Authorize, Don't Author" as on-ramp confirmed at §19 (line 260). Referenced in §37 context (pronoun role follows the same authorize-don't-author pattern of surfacing the system's interpretation for human confirmation).
- **Filename:** `inscript_addendum_v1b_design_resolutions.md` — domain `inscript` (provisional, pre-vault), class `addendum` (per skill table), version `v1b` (second addendum to v1, following v1a), subtitle `design_resolutions`. Verified against naming grammar in rmt-working-documents skill.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE DESIGN RESOLUTIONS ADDENDUM v1b*

*May 11, 2026*

*Eight questions. Eight answers. Zero guesses.*
*The grammar is now fully specified for v1.*
*Every word with more than one meaning has exactly one rule that resolves it.*
*The bounded vocabulary made this possible.*
*A language with 170,000 words could never do this.*
*A language with 28 can.*

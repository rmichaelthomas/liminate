# ADDENDUM
## Inscript Programming Language — Quoted-String Case Preservation
### v3b — Quoted Content Is Verbatim

**Status:** LOCKED — EXTENDS `inscript_addendum_v3a_event_driven_execution.md`
**Date:** May 13, 2026
**Author:** Rob Thomas / R. Michael Thomas (architect) and Claude (builder, drafting)
**Document type:** Addendum — supersedes v2c §91 (case normalization inside quotes) and extends v2c §90 (canonical rendering / conditional quoting). Quoted strings now preserve original case verbatim; the renderer adds a third trigger to its conditional-quoting rule so the round-trip property survives.
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** Extends `inscript_addendum_v3a_event_driven_execution.md` (May 12, 2026), which extends v2d/v2c/v2b/v2a/v1d/v1c/v1b/v1a and the Inception Checkpoint v1 (May 11–12, 2026). Continues from §126. This is the first patch-shaped addendum since v2.1 (the duplicate-field / `of`-on-list / list-operations-only patches embedded in v2a). It revises a single sub-decision (v2c §91) and tightens an adjacent one (v2c §90). No vocabulary changes, no new verbs or connectives, no execution-model changes.

---

## HOW TO READ THIS DOCUMENT

- §127 supersedes v2c §91 — quoted-string content is **preserved verbatim**, including case. The lexer no longer lowercases inside quotes.
- §128 extends v2c §90's conditional-quoting rule with a **case-preservation trigger** — the renderer emits quotes whenever the stored value differs from its lowercased form, so the round-trip property holds.
- §129 confirms **migration impact** — programs whose quoted strings were already all-lowercase are unaffected; programs that relied on `"In Progress"` matching data stored as `"in progress"` must align casing on both sides.
- §130 confirms the **vocabulary table is unchanged** — still 10 verbs, 14 connectives, 34 reserved words.
- §131 adds **test sentences 114–117** to the test suite.
- §132 extends the **build boundary**.

---

### §127 — QUOTED CONTENT IS VERBATIM (SUPERSEDES v2c §91)

**Decision: The lexer preserves the content of quoted strings exactly as written, including case, internal spacing, and punctuation. `"In Progress"` stores `In Progress`, not `in progress`. LOCKED. Supersedes v2c §91.**

**Why the v2c §91 rationale was wrong.** v2c §91 argued that quoted strings should lowercase "consistent with the language's universal case normalization" (v1d §57). That argument conflated two distinct uses of case folding:

| Use of case folding | Reason | Applies to |
|---|---|---|
| **Identifier normalization** | "Order" and "order" are the same name; "SHOW" and "show" are the same verb. Case carries no meaning. | Variable names, field names, vocabulary lookup — everything *outside* quotes. |
| **Data normalization** | A status code, label, proper noun, or external identifier sometimes uses case meaningfully. Folding silently loses information. | Quoted string values. |

The lexer's job is to recognize *language structure*. Inside quotes, the user has explicitly said "this is data, not language." Folding case at that point is the language reaching past its own boundary and editing user data. v2c §85 established quoting as the mechanism for "data the lexer should not interpret." Case folding violated that contract.

**Why the silent-mismatch concern was misweighted.** v2c §91 worried that `where status is "In Progress"` would silently fail to match data stored as `"in progress"`. That concern is real but cuts both ways: under case folding, `where status is "In Progress"` *succeeds* against `"in progress"` data — which means the user can't store proper-noun data (`"Los Angeles"`, `"DEFCON-1"`, `"PatientID-A1B2"`) or distinguish meaningful case (`"DRAFT"` vs `"draft"` status). The folded behavior makes mismatch impossible by *flattening the data*. That is not a fix; it is a loss of expressive range.

Quoting is the mechanism for values the lexer should not interpret. Case preservation is the natural completion of that mechanism. Programs that need case-insensitive matching can still use bare unquoted single-word values (`status as in-progress`) or hyphenated forms — those continue to lowercase under §22 and v1d §57.

**Punctuation, spaces, and case all preserved.** v2c §86 already specified that punctuation inside quotes is preserved verbatim. v3b §127 brings case under the same rule. The lexer's quoted-content handling is now uniform: **everything between the quote marks is data**, untouched.

**What is not changed.** All other v2c locks remain in force:
- §85 (quoting mechanism, hyphenation blessed) — unchanged.
- §86 (quote-state accumulation, unclosed-quote error) — unchanged; the only edit is that case is no longer folded.
- §87 (QUOTED_STRING valid in value positions only) — unchanged.
- §88 (literal display via `show "..."`) — unchanged; displayed output now carries the user's case.
- §89 (quoted reserved words bypass vocabulary) — unchanged.
- §90 (conditional rendering) — *extended* by §128, not retracted.
- §92 (empty quotes rejected) — unchanged.

The v2c §91 deferral of case-sensitive strings to "future type-system work (Q8)" is retired. The right place for case sensitivity turned out to be the quoting mechanism itself, not a parallel type. Q8 remains open for richer string operations (concatenation, substring, etc.); case is no longer part of it.

---

### §128 — CONDITIONAL QUOTING: THIRD TRIGGER (EXTENDS v2c §90)

**Decision: The renderer's conditional-quoting rule gains a third trigger. A string value is emitted with quotes when any of the following is true:**

1. **Multi-word** — the value contains a space (v2c §90, original trigger).
2. **Reserved word** — the value matches a vocabulary entry (v2c §90, original trigger).
3. **Case-bearing** — the value is not equal to its lowercased form (v3b, new trigger).

**Otherwise the value is emitted bare. LOCKED. Extends v2c §90.**

**Why the third trigger is mandatory.** Without it, the round-trip property breaks under case preservation. Consider `with status as "Active"`:

- The lexer produces `QUOTED_STRING("Active")`.
- The parser stores the literal `Active` in the AST.
- The renderer asks "is this multi-word? No. Is this a reserved word? No." Under the original §90 rule, the value emits bare: `with status as Active`.
- Re-lexing that canonical form produces an *unquoted* `active` (case-folded per §22).
- The re-parsed AST now stores `active`. The round-trip lost the capital `A`.

This is exactly the silent-corruption pattern v1c §52 (deterministic interpretation) forbids. The third trigger restores symmetry: when the lexer would lose information by re-folding case, the renderer keeps the quotes. The user sees the source-of-truth form: `with status as "Active"`.

**The rule is mechanically deterministic.** No heuristics, no proper-noun detection. The renderer asks: does `value == value.lower()`? If yes, the unquoted form re-lexes to the same value — emit bare. If no, the unquoted form re-lexes to a different value — emit quoted. The check is one comparison; no character classification or locale awareness is needed.

**Examples:**

| Stored value | Renderer output | Trigger |
|---|---|---|
| `active` | `with status as active` | None — single-word, lowercase, not reserved. |
| `Active` | `with status as "Active"` | **Case-bearing (§128).** |
| `in progress` | `with status as "in progress"` | Multi-word (§90). |
| `In Progress` | `with status as "In Progress"` | Multi-word **and** case-bearing — either trigger alone is enough. |
| `filter` | `with label as "filter"` | Reserved word (§90). |
| `DRAFT` | `with status as "DRAFT"` | Case-bearing — all-uppercase still differs from lowercased form. |
| `Los Angeles` | `with location as "Los Angeles"` | Multi-word and case-bearing. |

**Round-trip property reaffirmed.** v1a §33 locks: `parse(tokenize(render(ast))) == ast`. v3b §128 preserves this property under case-preserving lexing. Every AST whose string values carry case round-trips through quoted canonical form; every AST whose string values are all-lowercase round-trips through bare canonical form when the other triggers do not fire. Both branches are correct.

**`render_with_explicit_precedence` is unchanged.** The parens-on-mixed-and/or rendering path (used for AMBER messages, v1a §30) routes string emission through the same `_emit_string` helper, so the new trigger applies uniformly.

---

### §129 — MIGRATION IMPACT

**Decision: v3b is a behavior change for programs whose quoted strings contained uppercase characters; programs whose quoted content is already all-lowercase are unaffected. No vocabulary changes, no syntax changes, no error-message changes. LOCKED as the migration boundary.**

**What changes.**

| Construct | v2c behavior | v3b behavior |
|---|---|---|
| `with status as "In Progress"` | Stores `in progress` | Stores `In Progress` |
| `where status is "Active"` | Matches `"active"`, `"Active"`, `"ACTIVE"` (all stored as `active`) | Matches `"Active"` only |
| `show "Hello, World!"` | Displays `hello, world!` | Displays `Hello, World!` |
| `with status as "in progress"` (all lowercase) | Stores `in progress` | Stores `in progress` — no change |
| `with status as active` (unquoted) | Stores `active` | Stores `active` — no change |

**No existing test or example program changes behavior except where it explicitly relied on case-folding inside quotes.** Three test assertions in the v2c suite asserted lowercased quoted content (`hello, world!`, `in progress`, `section a: counts before filtering`); these are updated to assert verbatim content. No example programs in `examples/` relied on case folding — every example uses all-lowercase quoted content.

**Programs that need case-insensitive matching.** The two existing forms remain available:
- Bare unquoted single-word values (`status as in-progress`) — lexer lowercases per §22.
- Hyphenated multi-word names (`status as not-applicable`) — same path, no quoting needed.

A user who wants case-insensitive multi-word string matching should hyphenate the value at the source. Quoting now means "this exact string."

**No deprecation cycle.** v1d §61 explicitly noted single-token strings as a v1 constraint and forecast their relaxation; v2c §91 had no equivalent forecast. The decision being made now is that v2c §91 was the wrong call. Rather than deprecating it gradually, the addendum supersedes it cleanly — the right behavior is small, mechanical, and obvious, and no production programs run yet (v3a is the current language).

---

### §130 — VOCABULARY TABLE (UNCHANGED)

No vocabulary changes in v3b. The table from v3a §124 remains current:

- **10 verbs:** `remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each`, `choose`, `finish`.
- **14 connectives:** `with`, `from`, `to`, `as`, `where`, `of`, `and`, `or`, `not`, `the`, `if`, `otherwise`, `when`, `unless`.
- **34 reserved words** (verbs + connectives + operators + the `: ` delimiter family). Unchanged.

The lexer's quote-state mechanism (v2c §86) is unchanged in its structure; only the case-folding step is bypassed inside the accumulated content.

---

### §131 — TEST SENTENCES 114–117

Four new test sentences extend the test suite from v3a §125's sentence 113.

**Sentence 114 — Case preserved in storage and display.**

```
remember a task called t1 with status as "In Progress"
show status of t1
```

Expected output: `In Progress` (not `in progress`).

**Sentence 115 — Case-sensitive equality in `where`.**

```
remember a list of orders with
  remember an order called o1 with status as "Active" and total as 50
  remember an order called o2 with status as "active" and total as 75
keep the orders where status is "Active"
count the orders
```

Expected: count is `1` — only `o1` matches. Case-sensitive equality is the new behavior; under v2c both rows would have matched.

(Construct shown in pseudo-form for clarity — actual sentence uses v2d-locked syntax for list construction; the assertion is on case-sensitive `where`.)

**Sentence 116 — Round-trip canonical preserves case via re-quoting.**

```
remember a task called t1 with status as Active
```

This is a parse error under v2c (Active is unquoted and is not a reserved word, but the lexer lowercases it to `active`). Under v3b the same lowercasing applies — `Active` unquoted becomes `active`. The interesting round-trip is:

```
remember a task called t1 with status as "Active"
```

The canonical echo emits exactly the source form. Re-lexing the canonical produces the same AST. Round-trip holds via §128's third trigger.

**Sentence 117 — Unquoted tokens still lowercase (no regression).**

```
SHOW orders
Filter The Orders Where Status Is Active
```

Expected: both lines tokenize to all-lowercase identifiers and vocabulary (`show`, `filter`, `orders`, `the`, `where`, `status`, `is`, `active`). v3b changes nothing outside quotes. The §22 / v1d §57 case folding for identifiers and vocabulary lookup is preserved.

---

### §132 — BUILD BOUNDARY (EXTENDS v3a §126)

The build now includes:

1. The full v3a build (Phase 1 + Phase 2, listener mode, adapter contract, domain pack registration, finish verb, when/unless connectives).
2. v3b §127: `lexer.py` `_strip_and_lower` no longer lowercases tokens flagged `is_quoted=True`; quoted content flows through to the parser verbatim.
3. v3b §128: `renderer.py` `_emit_string` adds the third trigger to its conditional-quoting check: `s != s.lower()`.
4. v3b §131 test sentences 114–117 added to the integration test suite.

Implementation effort: two one-line code changes plus their docstrings, four new tests, three updated test assertions (the v2c suite tests that asserted lowercased quoted content). The full pytest suite passes at 667 tests after the change (665 v3a baseline + 2 new renderer tests; the lexer test was repurposed rather than added).

No new modules, no new AST nodes, no new error messages, no new vocabulary, no execution-model changes.

---

## WHAT IS LOCKED

This addendum locks:

- **Quoted content is verbatim (§127).** Lexer no longer folds case inside quotes. Punctuation, spacing, and case all preserved. Supersedes v2c §91.
- **Renderer's third quoting trigger (§128).** Emit quotes when the stored value is not equal to its lowercased form, so the round-trip property survives case preservation. Extends v2c §90.
- **Migration semantics (§129).** All-lowercase quoted content is unchanged. Mixed-case quoted content now stores verbatim. `where` equality on quoted values is case-sensitive.
- **Vocabulary unchanged (§130).** Still 10 verbs, 14 connectives, 34 reserved words.
- **Four new test sentences (§131).** Sentences 114–117.

This addendum does NOT modify any prior locked decision except v2c §91, which is explicitly superseded, and v2c §90, which is explicitly extended. Specifically:

- The two-phase execution model (v3a §107) is unchanged. Case preservation is a lexer concern; it applies identically in Phase 1 and Phase 2.
- All v3a `when`/`unless`/`finish` mechanics are unchanged. Quoted values inside action blocks and conditions preserve case.
- The quoting mechanism's other locks (v2c §85, §86, §87, §88, §89, §92) are unchanged.
- The reorderer's scope (v1d §55) is unchanged.
- The five-outcome taxonomy (v1c §50) is unchanged.
- Stepwise execution (v1d §56) is unchanged.
- Composition return values (v2b §76), generalized `of` (v2b §77), composition parameters (v2d §96–§98), and `choose` (v2d §99–§102) are all unchanged.
- The five-outcome amber/red/green model (v1a §30, v1c §50) is unchanged.

---

## RESUME PROMPT (Inscript Programming Language v3b)

*We are resuming from the Inscript Programming Language Quoted-String Case Preservation Addendum v3b (May 13, 2026), which extends v3a Event-Driven Execution (May 12, 2026), and back through v2d/v2c/v2b/v2a/v1d/v1c/v1b/v1a and the Inception Checkpoint v1 (all May 11–12, 2026). v3b is a small patch-shaped addendum: it supersedes v2c §91 (case normalization inside quotes) and extends v2c §90 (conditional rendering). **Core decision:** quoted-string content is now preserved verbatim — `"In Progress"` stores `In Progress`, not `in progress`. The lexer's case-folding step is bypassed inside the quoted-content accumulator; everything between quote marks is treated as data the language must not edit. **Renderer change:** the conditional-quoting rule gains a third trigger — emit quotes when the value differs from its lowercased form. Without this, `Active` would re-lex as `active` and the round-trip property would break. **Migration:** programs whose quoted content was already all-lowercase are unaffected. Programs that relied on `"In Progress"` matching data stored as `"in progress"` must align casing on both sides; the new equality on quoted values is case-sensitive. Case-insensitive matching is still available via bare unquoted single-word values and hyphenated forms (both of which the lexer lowercases per §22/v1d §57). **No vocabulary changes** — still 10 verbs, 14 connectives, 34 reserved words. **Four new test sentences** (114–117). The build boundary extends by two one-line code changes (`lexer.py` `_strip_and_lower`, `renderer.py` `_emit_string`) and four new tests; the v2c suite's three case-folding assertions are updated to verbatim. v3a's two-phase execution model, listener mode, adapter contract, and all reactive-mode semantics are unchanged. `transform`/`compare` remain deferred. The build specification is now eleven documents: inception checkpoint v1, addenda v1a/v1b/v1c/v1d/v2a/v2b/v2c/v2d/v3a/v3b, plus the 117-sentence test suite.*

---

## PROVENANCE NOTE

This addendum was verified against:

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026):
  - §22 (lexer specification) — case folding is specified for vocabulary lookup and identifier normalization. Quoted content is data, not language structure; v3b §127 confines case folding to the language-structure path.
  - §25 (Q8, type system) — the v2c §91 deferral of case sensitivity to Q8 is retired. Q8 remains open for string operations (concatenation, substring); case is no longer part of it.
- **`inscript_addendum_v1a_pre_build.md`** (May 11, 2026):
  - §33 (canonical rendering, round-trip property) — v3b §128's third trigger preserves the round-trip invariant under case preservation.
- **`inscript_addendum_v1c_implementation_hardening.md`** (May 11, 2026):
  - §52 (deterministic interpretation) — case preservation makes data flow more deterministic, not less: the value the user wrote is the value the program sees.
- **`inscript_addendum_v1d_build_boundary.md`** (May 11, 2026):
  - §57 (symbol table names are stored lowercase) — applies to identifier names, not quoted-string values. v3b §127 sharpens the distinction.
  - §61 (single-token strings, superseded by v2c §85) — historical context for the staged relaxation of string-handling constraints.
- **`inscript_addendum_v2c_multi_word_strings.md`** (May 12, 2026):
  - §85 (quoting mechanism, hyphenation blessed) — unchanged. v3b completes the "data the lexer should not interpret" contract by adding case to the verbatim-content guarantee.
  - §86 (lexer quote-state accumulation) — structurally unchanged; case-folding step bypassed.
  - §87 (QUOTED_STRING in value positions) — unchanged.
  - §88 (literal display via `show "..."`) — unchanged; displayed output now carries case.
  - §89 (quoted reserved words as data) — unchanged.
  - §90 (canonical rendering, conditional quoting) — extended by v3b §128 (third trigger).
  - §91 (case normalization inside quotes) — **superseded by v3b §127.**
  - §92 (empty quotes rejected) — unchanged.
- **`inscript_addendum_v3a_event_driven_execution.md`** (May 12, 2026):
  - §107–§126 — entirely unchanged. v3b is a lexer/renderer patch; it touches no execution-model surface.

- **Internal consistency verification** (May 13, 2026): the round-trip property (`parse(tokenize(render(ast))) == ast`) was verified by induction across the renderer's emission paths — bare emission re-lexes to the lowercased form (which equals the AST value when the case-bearing trigger does not fire), quoted emission re-lexes to the verbatim content (which always equals the AST value). Full pytest suite passes at 667 tests.

- **Filename:** `inscript_addendum_v3b_quoted_string_case_preservation.md` — domain `inscript` (provisional, pre-vault), class `addendum`, version `v3b` (second addendum in the v3 series, a patch-shaped revision rather than a feature addendum), subtitle `quoted_string_case_preservation`.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE QUOTED-STRING CASE PRESERVATION ADDENDUM v3b*

*May 13, 2026*

*The original §91 said: quoted strings lowercase, consistent with the language.*
*The new §127 says: quoted strings are verbatim, consistent with the user.*
*The lexer was reaching past its boundary. Now it stops at the quote mark.*
*Two lines of code. One assumption corrected.*

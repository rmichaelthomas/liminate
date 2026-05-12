# ADDENDUM
## Inscript Programming Language — Dogfooding Resolutions
### v2a — Non-Destructive Filter, Field Access, Multi-Field Display

**Status:** LOCKED — EXTENDS `inscript_addendum_v1d_build_boundary.md`
**Date:** May 12, 2026
**Author:** Rob Thomas / R. Michael Thomas
**Document type:** Addendum — adds one verb (`keep`), one connective (`of`), one new context rule for `and`, two error/rendering improvements; defers multi-word strings to a dedicated checkpoint
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** Extends `inscript_addendum_v1d_build_boundary.md` (May 11, 2026), which extends v1c/v1b/v1a/the Inception Checkpoint (all same date). Continues from §66. Implements decisions A–D from the v2 Design Triage (`inscript_v2_design_triage_2026_05_12.md`, May 12, 2026), which triaged the eight v2-design items from the v1 Dogfooding Gap Inventory (`inscript_gap_inventory_2026_05_12_v1_dogfooding.md`, same date). This addendum locks five resolutions and defers one (D7).

---

## HOW TO READ THIS DOCUMENT

- §67–§71 each lock one resolution. §72 records the D7 deferral.
- §73 collects the updated vocabulary counts in one table.
- §74 adds test sentences 49–59 to the test suite (which ended at sentence 48 in v1d §65).
- The five locked decisions and the one deferral correspond 1:1 to gap-inventory items D2, D4, D1, D5, D6, and D7. Cross-references to the gap inventory and triage are in §76.
- The build boundary in v1d §66 is extended (not replaced) — v1d's "What v1 builds" surfaces remain in v2a. The new additions extend the parser, analyzer, interpreter, renderer, vocabulary, and test suite. No prior locked decision is modified.

---

### §67 — `keep` VERB: NON-DESTRUCTIVE FILTER

**Decision: `keep` is a new verb that filters a list and returns the matching items as a fresh list without modifying the source. Its parse-time shape is identical to `filter` (target + `where` + condition). The two verbs differ only in interpreter behavior: `filter` mutates the symbol-table entry in place (§24 line 478); `keep` returns a new list and leaves the source untouched. LOCKED as v2a verb addition.**

The gap in v1 (Dogfooding Inventory D2): every multi-pass analysis of a list required re-typing the entire `remember a list called X with item-1 and item-2 and ...` statement before each filter, because `filter` is destructive. Programs 2, 3, and 4 of the dogfooding pass demonstrated the cost — Program 2 forced a 30-item re-type to run sequential probes; Program 3 demonstrated that compositions wrapping a destructive filter silently no-op on the second call (D3).

The decision in the v2 Design Triage §3 was Path A: add a non-destructive verb rather than overload `from` with a snapshot meaning. Three reasons:

1. **Concept-layer alignment (inception §10).** `keep` is itself a meaningful concept in the business-rules domain — "keep the rows that match." Adding it to the base vocabulary is in keeping with the language's "name what people are trying to do" principle.
2. **Disambiguation hygiene.** Adding a snapshot meaning to `from` would have given it a fourth context rule, compounding v1b §43's complexity. A new verb has a clean signature with no context-dependent meanings.
3. **`filter` keeps its word-salad-tested role.** `filter the orders` reads as "the orders are now filtered" — destructive intuition. `keep` reads as "the matching ones are kept" — non-destructive intuition. The two verbs name two genuinely different operations.

**Verb signature** (extending inception §17):

```
keep -> target + condition
```

Identical to `filter`. The parser shares the implementation (`_parse_filter_shape`) between the two verbs; only the AST node type and interpreter execution path differ.

**Auto-show and capture.** Per inception §24's auto-show rule, a standalone `keep` displays the matching items. The result can also be captured via the `remember ... from <verb phrase>` recursive-descent mechanism (v1b §43):

```
keep the orders where total is above 50                            # auto-shows
remember the matches called big from keep the orders where total is above 50
```

In the capture form, the auto-show is suppressed (the value flows into the surrounding `remember` instead) and `big` is bound to the matching list. In both forms, `orders` is unchanged.

**Empty result.** When no records match, `keep` returns an empty list. The auto-show emits an empty line (per v1b §42's comma-separated list format). The source is still untouched.

**Composition behavior — D3 resolution.** Named compositions wrapping `keep` are reusable: calling them repeatedly always operates on the unchanged source data. This dissolves the D3 gap. Example:

```
remember how to find-big: keep the orders where total is above 50
find-big                # auto-shows matches; orders unchanged
find-big                # same matches; orders still unchanged
```

**Error behavior.** `keep` on a non-list target produces the semantic error "I can only keep from a list. '<name>' is <type>." — symmetric with `filter`'s message (v1d §65 sentence 36).

**Copy semantics.** `keep` deep-copies each matching item into the result list, consistent with inception §24's copy-semantics invariant. Modifying the result does not modify the source.

---

### §68 — `of` CONNECTIVE: SINGLE-RECORD FIELD ACCESS

**Decision: `of` is a new connective that, when used after a field name in a `show` target position, accesses one field of one record. The form is `show <field> of <record>`. LOCKED as v2a connective addition.**

The gap in v1 (Dogfooding Inventory D4): given `remember an order called order1 with total as 75 and status as active`, v1 had no way to display *one field* of `order1`. The workarounds (wrap the record in a list, iterate via `each`) were verbose for a single record.

The decision in the v2 Design Triage §4 was `of` over `'s` (which would have introduced an apostrophe-s lexer token, breaking the whitespace-splitting rule in inception §22 and v1c §46) and over a fourth `from` meaning (which would have compounded v1b §43's overload). New vocabulary (one reserved word) was cheaper than either lexer changes or further `from` disambiguation.

**Parser shape.** Inside `_parse_show`, after consuming the first unknown token (the field name), if the next token is `of` (CONNECTIVE), the parser consumes it and then consumes the next token as the record name. The `ShowNode` AST gains an optional `record_name: str | None` field — when populated, the `target` (a `NameRef`) is interpreted as the field name and `record_name` as the symbol to look it up on.

**Semantic checks.** Three error paths:

1. **Record not in symbol table:** `show total of ghost` → "I can't find 'ghost'. You might need to 'remember' it first."
2. **Symbol exists but is not a record:** `show something of age` (where `age` is a number) → "'of' needs a record. 'age' is a number."
3. **Record exists but lacks the field:** `show missing of order1` → "'order1' doesn't have a field called 'missing'."

**Display.** The value is rendered per inception §24 / v1b §42 scalar formats (numbers as-is, strings without quotes).

**Forward compatibility with D7 (multi-word strings).** When D7 is taken up in its own checkpoint (§72), `show "total amount" of order1` should resolve the same as `show total-amount of order1` once a multi-word approach is chosen. `of` operates on the *resolved field name*; D7 will extend what constitutes a valid field reference but should not require revisiting §68.

**Forward compatibility with field-access chaining.** `show field-a of field-b of record1` is not specified in v2a — `of` is left-associative with a single record name on the right. If nested records appear in a future v2 spec, the precedence rule for chained `of` is open. For v2a, `of` is a single-level field access.

---

### §69 — FIFTH `and` CONTEXT RULE: MULTI-FIELD DISPLAY IN `each ... show`

**Decision: Inside an `each ... show` body, `and` between unknown tokens means "list of fields to display." Per-record output is `field1: value1, field2: value2, ...` — one line per record. LOCKED as fifth `and` context rule, extending inception §21 and v1b §44.**

The gap in v1 (Dogfooding Inventory D1): `each the docs show words and class` was a parse error because none of the four pre-existing `and` meanings in §21 covered "list of fields in a `show` clause." The four existing meanings (list construction in `with`, compound condition in `where`, operation sequencing after a complete verb phrase, record field continuation in `with...as`) all required either a different clause context or a different next-token category.

**The fifth rule** (extending inception §21):

| Context | Meaning | Disambiguation |
|---|---|---|
| Inside `each ... show` after a field-name UNKNOWN, next token is UNKNOWN | Multi-field display | Parser state = inside `each` clause AND inside `show`; next token = UNKNOWN (not VERB → which would be operation sequencing) |

**Parser shape.** The parser passes an `in_each` flag to `_parse_show` based on the clause-context stack (v1c §51). When `in_each` is true, after consuming the first UNKNOWN field, the parser checks for `and <UNKNOWN>` repetitions and collects each additional UNKNOWN into the `ShowNode.extra_fields` list. Operation sequencing (`and <VERB>`) still wins — if the token after `and` is a verb, the parser returns to the outer operation loop instead.

**Semantic checks.** All listed fields must exist on every record in the iterated list. The error message is symmetric with the existing schema-homogeneity message (v1d §60):

```
each the docs show words and nonexistent
# → "Not every item in 'docs' has a field called 'nonexistent'."
```

**Display.** For each record, the interpreter emits a single line with `field: value` pairs joined by `, ` — the same format used by `show` on a full record (v1b §42), but filtered to only the listed fields.

**Single-field path unchanged.** `each the docs show words` still emits one bare value per record (v1b §42 / v1c §49). The fifth rule activates only when `and <UNKNOWN>` follows the first field name inside `each`.

**Outside `each`, the construct is rejected.** `show total and status of order1` does not parse as multi-field show — `show` outside `each` does not enter the multi-field path, and `and` after `show <name>` is interpreted as operation sequencing (which fails when followed by an unknown rather than a verb). For tabular display of a single record's fields, the user has two options: wrap the record in a one-item list and iterate, or use `show <field> of <record>` (§68) per field.

**Interaction with the existing four `and` rules:** the fifth rule does not collide with any of them. Inside `each ... show`, none of the four existing contexts can fire — there is no `with` clause, no `where` clause, no complete verb phrase preceding the `and` (the `and` is inside the `show` sub-operation), and no `with...as` clause. The clause-context check (`in_each` AND parsing `show`) is sufficient to isolate the new rule.

---

### §70 — COMPOSITION CHAINING ERROR MESSAGE (D5)

**Decision: When the parser detects a named-composition call followed by `from`, it emits a v1-specific deferral message rather than the generic "I didn't expect 'from' here." LOCKED as v2a parser error wording.**

The gap in v1 (Dogfooding Inventory D5): `find-large from docs` produced the generic *"Error: I didn't expect 'from' here."* The deferral itself was already locked in v1b §41 (composition chaining is deferred to v2 alongside composition parameters, per Q9). The error did not signal that the construct was a deferred feature; users could not tell whether they had typo'd or used an unsupported feature.

**The new message** (locked here):

```
Composition chaining isn't supported yet. Call '<name>' on its own line.
```

The detection lives at the v1b §41 composition-fallback site in `_parse_one_operation`. After consuming the composition name, the parser peeks for `from`. If found, the deferral message fires before control returns to the outer parser (which would otherwise produce the generic "didn't expect 'from'" error).

**No spec change beyond wording.** Composition chaining remains v2-deferred per v1b §41 / Q9. This addendum only improves the error path so users understand they have written a deferred feature rather than a malformed sentence.

---

### §71 — DESCRIPTOR PRESERVATION IN CANONICAL RENDERING (D6)

**Decision: The user's descriptor (zero or more unknown words between the article and `called`) is carried through the `remember` AST nodes and emitted verbatim in canonical rendering. When the user provided no descriptor, the renderer falls back to the inferred type label (`value` / `list` / `record`). The descriptor is semantically decorative (v1b §36, unchanged) — it does not affect parsing or analysis. LOCKED as v2a renderer behavior.**

The gap in v1 (Dogfooding Inventory D6): `remember a domain called mobius with docs as 91 and words as 381476` was rendered as `remember a record called mobius with docs as 91 and words as 381476`. The user's word `domain` (which contributes to readability for a domain expert) was replaced with the type-system-internal term `record`. The prose-as-syntax invariant (v7.5g §13) calls for preserving the user's voice; replacing their descriptor was a small but recurring loss.

**AST change.** Each `remember` AST node (`RememberValueNode`, `RememberListNode`, `RememberRecordNode`) gains an optional `descriptor: str | None` field. The field is excluded from `__eq__` because descriptors carry no semantic weight (v1b §36) — two ASTs that differ only in descriptor are equivalent.

**Parser change.** `_consume_remember_intro` now captures the verbatim sequence of unknown words between the article and `called` (joined by spaces) and returns it as the descriptor alongside the existing `saw_list` flag. The `saw_list` flag still forces singleton-list construction for `remember a list called X with Y` (v1d §65 sentence 38, unchanged).

**Renderer change.** Each `remember` node's renderer uses `node.descriptor` when present, falling back to the inferred type label (`value` / `list` / `record`) when the descriptor is `None`. The leading article switches between `a` and `an` based on the first letter of the descriptor (vowel → `an`).

**Round-trip preservation.** Parsing `remember a domain called mobius ...` produces an AST with `descriptor = "domain"`. Rendering this AST emits `remember a domain called mobius ...`. Re-parsing produces the same AST. The round-trip property in renderer.py is preserved.

**Multi-word descriptors.** `remember a big number called age with 30` produces `descriptor = "big number"`. The renderer emits it verbatim. The article picks `a` (consonant-initial first word).

**No interaction with D7.** Multi-word descriptors are *unknown words at parse time*, not string values. The single-token-string constraint (v1d §61) and its D7 deferral (§72) apply to value positions, not descriptor positions.

---

### §72 — D7 DEFERRAL: MULTI-WORD STRINGS

**Decision: D7 (multi-word string values) is explicitly deferred to a dedicated v2 checkpoint. No multi-word string mechanism is added in v2a. LOCKED as v2a deferral.**

The v2 Design Triage §5 identified D7 as touching more spec surfaces than any other v2-design item: the lexer's whitespace-splitting rule (inception §22, v1c §46), the prose-as-syntax invariant (v7.5g §13), the reserved-word list (v1a §29, v1c §47), and domain-pack collision rules (§19 Mechanism 1). The triage recommended a dedicated checkpoint with external review (the same pattern used for v1a/v1b/v1c/v1d).

**Three candidate approaches** (catalogued in the triage §5):

| Approach | Example | Tradeoff |
|---|---|---|
| **Quoting** | `with status as "in progress"` | Adds syntax marks; the cleanest mechanically, the noisiest visually for non-programmers — quote marks are the closest thing to "programming syntax" the language would have. |
| **Hyphenation convention** | `with status as in-progress` | Already works in v1/v2a. Punts on the prose question by changing the prose. Adopted ad-hoc in dogfooding for `gap-inventory`, `find-large`, `nums-copy`. |
| **Multi-word phrase spans** | `with status as in progress` | Lexer accumulates known multi-word phrases from a registry. Reads as natural prose. Requires phrase registry, conflict resolution with single words, stable definition of "known," and domain-pack-aware reloading. |

**The v1 hyphenation workaround remains valid in v2a.** Programs that need multi-word category names (e.g., `gap-inventory`, `in-progress`) should continue to hyphenate. The dogfooding pass adopted this convention throughout without friction for the English-speaker reader.

**Interaction with v2a §68 (`of`).** `show <field> of <record>` works with single-token field names in v2a. When D7 is taken up, the chosen approach will extend what constitutes a valid field reference (e.g., `show "total amount" of order1` if quoting wins). The `of` connective itself does not need revisiting in the D7 checkpoint.

**Implementation note.** The vocabulary module includes a `D7_DEFERRED` comment near the reserved-word tables (`src/inscript/vocabulary.py`) to flag the open design question for future implementers. No code change is required.

---

### §73 — UPDATED VOCABULARY TABLE

Updated from inception §11 / v1c §47.

| Category | Words | Count |
|---|---|---|
| **Verbs** | `remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each` | **8** |
| **Connectives** | `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`, `of` | **10** |
| **Operators** | `is`, `above`, `below`, `not` (single-word) | 4 |
| **Multi-word operator component** | `equal` (combines with `to` per inception §22) | 1 |
| **Articles** | `the`, `a`, `an` | 3 |
| **v2 deferred verbs** | `transform`, `choose`, `compare` | 3 |
| **v2 deferred connectives** | `when`, `unless` | 2 |
| **Total reserved** | | **31** |

Delta from v1c §47: +1 verb (`keep`, §67), +1 connective (`of`, §68). Reserved word count was 29 in v1c; now 31.

**No words were removed.** All v1 reserved words remain reserved.

**Verb signatures** (extending inception §17):

| Verb | Slots |
|---|---|
| `remember` | name, value |
| `show` | target |
| `filter` | target, condition |
| `keep` | target, condition |
| `count` | target |
| `gather` | name, from, to |
| `combine` | target |
| `each` | collection, action |

`keep`'s signature is structurally identical to `filter`'s; the parser shares its shape (§67).

---

### §74 — NEW TEST SENTENCES

Extending the test suite from sentence 48 (v1d §65) to sentence 59.

**Sentence 49 — `keep` basic (auto-shows; source unchanged)**
```
remember an order called order1 with total as 75 and status as active
remember an order called order2 with total as 30 and status as pending
remember a list called orders with order1 and order2
keep the orders where total is above 50
count the orders
```
→ Line 4: `total: 75, status: active` (auto-shown match)
→ Line 5: `2` (orders is unchanged — D2 / §67 resolution)
**Tests:** §67 — `keep` does not modify the source list.

**Sentence 50 — `keep` captured via `remember ... from`**
```
remember an order called o1 with total as 75 and status as active
remember a list called orders with o1
remember the matches called big from keep the orders where total is above 50
show big
count the orders
```
⊕ Symbol table: `big` = list with 1 matching record.
→ Line 4: `total: 75, status: active`
→ Line 5: `1`
**Tests:** §67 — `keep` integrates with v1b §43's recursive-descent capture path. Source `orders` (1 item) is preserved.

**Sentence 51 — `keep` on a scalar (semantic error)**
```
remember a number called age with 30
keep the age where each is above 5
```
⚠ Outcome 5: "I can only keep from a list. 'age' is a number."
**Tests:** §67 — `keep` error wording, symmetric with `filter`'s in v1d §65 sentence 36.

**Sentence 52 — `keep` in a composition is reusable (D3 resolution)**
```
remember an order called o1 with total as 75 and status as active
remember an order called o2 with total as 30 and status as active
remember a list called orders with o1 and o2
remember how to find-big: keep the orders where total is above 50
find-big
find-big
count the orders
```
→ Both `find-big` calls auto-show the same single match.
→ Line 7: `2` (orders unchanged after both calls)
**Tests:** §67 — D3 (destructive-composition single-use problem) dissolves when the composition wraps `keep` instead of `filter`.

**Sentence 53 — `show <field> of <record>`**
```
remember an order called order1 with total as 75 and status as active
show total of order1
show status of order1
```
→ Line 2: `75`
→ Line 3: `active`
**Tests:** §68 — basic field access. Both number and string field types.

**Sentence 54 — Missing field in `of` access (semantic error)**
```
remember an order called order1 with total as 75 and status as active
show missing of order1
```
⚠ Outcome 5: "'order1' doesn't have a field called 'missing'."
**Tests:** §68 — record-exists, field-missing error.

**Sentence 55 — Missing record in `of` access (semantic error)**
```
show total of ghost
```
⚠ Outcome 5: "I can't find 'ghost'. You might need to 'remember' it first."
**Tests:** §68 — record-not-found error. Reuses the v1 name-not-found wording for consistency.

**Sentence 56 — `of` on a non-record (semantic error)**
```
remember a number called age with 30
show something of age
```
⚠ Outcome 5: "'of' needs a record. 'age' is a number."
**Tests:** §68 — type check on the operand of `of`.

**Sentence 57 — `each ... show <a> and <b>` (multi-field display)**
```
remember a doc called d1 with class as checkpoint and words as 1000
remember a doc called d2 with class as addendum and words as 2000
remember a list called docs with d1 and d2
each the docs show words and class
```
→ Line 4 (first record): `words: 1000, class: checkpoint`
→ Line 4 (second record): `words: 2000, class: addendum`
**Tests:** §69 — the fifth `and` context rule.

**Sentence 58 — Multi-field show with a missing field (semantic error)**
```
remember a doc called d1 with class as checkpoint and words as 1000
remember a list called docs with d1
each the docs show words and nonexistent
```
⚠ Outcome 5: "Not every item in 'docs' has a field called 'nonexistent'."
**Tests:** §69 — semantic check extends across all listed fields, using the schema-homogeneity error wording (v1d §60).

**Sentence 59 — Composition chaining error message (D5)**
```
remember an order called order1 with total as 75 and status as active
remember a list called orders with order1
remember how to find-big: filter the orders where total is above 50
find-big from orders
```
⚠ Outcome 4 (parse error): "Composition chaining isn't supported yet. Call 'find-big' on its own line."
**Tests:** §70 — the v1 deferral is now surfaced with a specific message rather than the generic "didn't expect 'from'" error.

---

### §75 — UPDATED BUILD BOUNDARY (extension to v1d §66)

The v1 build boundary (v1d §66) is extended — not replaced — by v2a:

| Component | v2a additions |
|---|---|
| **Lexer** | `keep` and `of` recognized as VERB and CONNECTIVE respectively via existing vocabulary lookup; no lexer rule changes |
| **Parser** | `keep` shares `_parse_filter_shape` with `filter` (KeepNode); `_parse_show` accepts `<field> of <record>` and multi-field `<field> and <field>...` (the latter only inside `each`); `_consume_remember_intro` returns the verbatim descriptor; composition-call fallback emits the D5 deferral message when followed by `from` |
| **Semantic analyzer** | `_check_keep` mirrors `_check_filter`; `_check_show` validates `of` (record exists, is a record, has the field) and multi-field show (each listed field exists on every record) |
| **Interpreter** | `_exec_keep` returns a copied list of matches without mutating the source; `keep` is also handled in `_evaluate_expression` for the `remember ... from keep ...` capture path; `_exec_show` extracts the named field for `of` and emits `field: value, ...` lines for multi-field `each ... show` |
| **Canonical renderer** | `keep <target> where <condition>` form; `show <field> of <record>` form; `show <field> and <field> and ...` form inside `each`; descriptor preserved on all three `remember` shapes with vowel-sensitive article |
| **Result interface** | Unchanged. Five outcomes per v1c §50 still cover every statement |
| **CLI wrapper** | Unchanged from v1d §66 + post-v1 patches (`--test` accepts any position; canonical not re-emitted on amber-confirm) |

**What v2a does NOT build:**

- Multi-word strings (D7, §72)
- `transform` / `choose` / `compare` (still v2)
- `when` / `unless` and event-driven execution (still v2)
- Composition parameters and `from` chaining (still v2 / Q9, per v1b §41)
- Field-access chaining (`field-a of field-b of record1`) — single-level only (§68)
- Tile interface, proposal engine, domain packs (Branch C/E)

---

## WHAT IS LOCKED

This addendum locks:

- **`keep` verb (D2 / §67).** Non-destructive filter. Same parse-time shape as `filter`. Source list unchanged. Integrates with `remember ... from ...` capture. Composition reusability (D3) dissolves as a side effect. Word count: 7 verbs → 8.
- **`of` connective (D4 / §68).** Single-record field access via `show <field> of <record>`. Single-level only. Three semantic checks (record exists, is a record, has the field). Connective count: 9 → 10.
- **Fifth `and` context rule (D1 / §69).** Inside `each ... show`, `and` between unknowns collects additional field names. Display format: `field: value, ...` per record. The four existing `and` meanings (§21) are unchanged.
- **Composition chaining error message (D5 / §70).** Specific v1-deferral wording replaces the generic "didn't expect 'from'" error. No semantic change — composition chaining remains v2-deferred per v1b §41.
- **Descriptor preservation (D6 / §71).** User's descriptor between article and `called` is preserved through the AST and emitted in canonical rendering. Falls back to inferred type label when no descriptor. Excluded from AST equality (descriptors remain decorative per v1b §36).
- **D7 deferral (§72).** Multi-word strings are explicitly deferred to a dedicated checkpoint with three candidate approaches documented (quoting, hyphenation, multi-word phrase spans). The v1 hyphenation workaround remains valid.
- **Updated vocabulary counts (§73).** 8 verbs, 10 connectives, 31 reserved words total (was 7/9/29 in v1c).
- **Eleven new test sentences (§74).** Sentences 49–59 extending the test suite from 48.

This addendum does NOT modify any prior locked decision. Specifically:
- `filter` remains destructive (v1d §66 / inception §24).
- `combine` remains numeric-only and non-destructive (v1b §38, §39).
- Copy semantics unchanged (inception §24 line 486).
- Single-token strings still locked for value positions (v1d §61).
- Stepwise execution unchanged (v1d §56).
- The five-outcome taxonomy (v1c §50) is unchanged.
- The reorderer's v1 scope (v1d §55) is unchanged.

---

## RESUME PROMPT (Inscript Programming Language v2a)

*We are resuming from the Inscript Programming Language Dogfooding Resolutions Addendum v2a (May 12, 2026), which extends v1d Build Boundary, v1c Implementation Hardening, v1b Design Resolutions, v1a Pre-Build, and the Inception Checkpoint v1 (all May 11, 2026). v2a implements decisions A–D from the v2 Design Triage (May 12, 2026), which triaged the eight v2-design items from the v1 Dogfooding Gap Inventory (same date). v2a locks five resolutions and defers one. The five locked: (1) `keep` verb — non-destructive filter, same signature as `filter` but returns a fresh list without mutating the source; auto-shows matches; integrates with `remember ... from keep ...` capture; D3 (composition single-use) dissolves as a side effect. (2) `of` connective — single-record field access via `show <field> of <record>`; three semantic checks; single-level only. (3) Fifth `and` context rule — inside `each ... show`, `and` between unknowns collects additional field names; output format `field: value, ...` per record. (4) Composition chaining error message — specific v1-deferral wording instead of generic "didn't expect 'from'"; composition chaining remains v2-deferred per v1b §41. (5) Descriptor preservation — the user's word between article and `called` is preserved through the AST and emitted in canonical rendering; falls back to inferred label when absent. The one deferral: D7 (multi-word strings) → dedicated checkpoint with external review; the hyphenation workaround remains valid. Vocabulary counts: 8 verbs (+keep), 10 connectives (+of), 31 reserved words total (was 29 in v1c). Eleven new test sentences (49–59). The v1d build boundary is extended, not replaced. Build specification is now six documents: inception checkpoint v1, addenda v1a/v1b/v1c/v1d/v2a, plus the 59-sentence test suite. The next concrete pre-spec work is the D7 checkpoint.*

---

## PROVENANCE NOTE

This addendum was verified against:

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026):
  - §10 (concept-layer vocabulary) — referenced in §67's rationale for adding `keep` as a meaningful concept.
  - §11 (vocabulary table) — extended in §73 with `keep` and `of`.
  - §17 (verb signatures, slot-filling) — `keep`'s signature in §73 mirrors `filter`'s.
  - §19 Mechanism 1 (domain packs, vocabulary scaling) — referenced in §72's D7 collision discussion.
  - §20 (word salad test) — referenced in §67/§68 to validate `keep` and `of` as readable English.
  - §21 (four `and` context rules) — extended in §69 with the fifth rule.
  - §22 line 432 (whitespace splitting), referenced in §72 for D7's lexer-rule impact.
  - §24 (auto-show, in-place filter, copy semantics) — referenced in §67 for `keep`'s auto-show behavior and copy semantics.
- **`inscript_addendum_v1a_pre_build.md`** (May 11, 2026):
  - §29 (reserved word list) — extended in §73; count was 28 (v1a), corrected to 29 (v1c §47), now 31.
  - §30 (mixed-precedence amber) — unchanged; still applies to `keep`'s where-clauses.
  - §33 (canonical prose rendering) — extended in §71 to include the descriptor.
- **`inscript_addendum_v1b_design_resolutions.md`** (May 11, 2026):
  - §36 (descriptors are decorative) — referenced in §71 (still semantically decorative; only rendering changes).
  - §38, §39 (`combine` semantics) — unchanged.
  - §41 (composition call fallback) — referenced in §70 (composition chaining stays deferred; only error wording changes).
  - §42 (display formats) — referenced in §67/§68/§69 (multi-field display uses the field:value format from §42).
  - §43 (`from` disambiguation) — referenced in §67 (the recursive-descent path that captures `keep`'s result).
  - §44 (complete parser disambiguation ruleset) — extended in §69 with the fifth `and` rule.
- **`inscript_addendum_v1c_implementation_hardening.md`** (May 11, 2026):
  - §46 (vocabulary words cannot be string values) — referenced in §72 (D7's impact on lexer rules).
  - §47 (`an` article, reserved word count corrected to 29) — extended in §73 to 31.
  - §49 (iterator context for `each`) — `each ... show` multi-field uses the iterator context unchanged.
  - §50 (five-outcome taxonomy) — `keep`/`of`/multi-field show all map to Outcomes 1 or 5; no new categories.
  - §51 (parser lookahead + clause-context tracking) — §69 uses the clause-context stack to detect `in_each`.
- **`inscript_addendum_v1d_build_boundary.md`** (May 11, 2026):
  - §55 (reorderer scope) — unchanged; `keep` parses in canonical order like `filter`.
  - §56 (stepwise execution) — unchanged.
  - §57–§64 (case normalization, duplicate names, list homogeneity, schema homogeneity, single-token strings, descending ranges, range cap, structured results) — all unchanged.
  - §60 (record schema homogeneity) — §69's multi-field validation reuses the schema-homogeneity error wording.
  - §61 (single-token strings) — referenced in §72.
  - §65 (test sentences 35–48) — extended in §74 with sentences 49–59.
  - §66 (build boundary) — extended (not replaced) in §75.
- **`inscript_gap_inventory_2026_05_12_v1_dogfooding.md`** (May 12, 2026):
  - D1, D2, D3, D4, D5, D6, D7 surfaced by the seven dogfooding programs. v2a resolves D1, D2, D4, D5, D6; D3 dissolves as a side effect of D2; D7 is deferred.
- **`inscript_v2_design_triage_2026_05_12.md`** (May 12, 2026):
  - §2 re-tiering table — D5/D6 demoted to v1.1-patch (shipped here as §70/§71 per architect direction to bundle in one addendum); D1/D2/D4 grouped here as §67/§68/§69; D7 deferred per §72.
  - §3 D2 Path A vs Path B — architect chose Path A (`keep`); locked in §67.
  - §4 D4 form choice — architect chose `of`; locked in §68.
  - §5 D7 dedicated checkpoint — locked as a deferral in §72.
- **External pattern verification:** No external review (Gemini/ChatGPT) was solicited for this addendum because the changes are scoped extensions of locked decisions rather than new architecture. A dedicated checkpoint for D7 (per §72) is the appropriate locus for the next external review.
- **Filename:** `inscript_addendum_v2a_dogfooding_resolutions.md` — domain `inscript` (provisional, pre-vault), class `addendum`, version `v2a` (first addendum in the v2 series), subtitle `dogfooding_resolutions`. Naming pattern matches v1a–v1d.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE DOGFOODING RESOLUTIONS ADDENDUM v2a*

*May 12, 2026*

*The dogfooding pass surfaced eight gaps the 48-sentence test suite didn't.*
*Five become spec — one verb, one connective, one new `and` rule, two improved messages.*
*One becomes its own checkpoint.*
*The build boundary expands by exactly what was learned and no more.*

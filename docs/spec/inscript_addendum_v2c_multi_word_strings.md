# ADDENDUM
## Inscript Programming Language — Multi-Word Strings
### v2c — The Quoting Mechanism

**Status:** LOCKED — EXTENDS `inscript_addendum_v2b_composition_returns.md`
**Date:** May 12, 2026
**Author:** Rob Thomas / R. Michael Thomas
**Document type:** Addendum — resolves D7 (multi-word strings) by introducing a quoting mechanism for value positions, formally blesses hyphenation as the convention for names and field names, and locks seven sub-decisions from the D7 checkpoint analysis
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** Extends `inscript_addendum_v2b_composition_returns.md` (May 12, 2026), which extends v2a/v1d/v1c/v1b/v1a and the Inception Checkpoint v1 (May 11, 2026). Continues from §84. Resolves the D7 deferral catalogued in the v1 dogfooding gap inventory, triaged in the v2 Design Triage §5, explicitly deferred in v2a §72, and confirmed as the next open question in v2b's resume prompt. The D7 checkpoint analysis (`inscript_checkpoint_v2c_multi_word_strings.md`, May 12, 2026) evaluated three approaches against every locked spec surface; the architect approved the recommended approach and all sub-decisions. This addendum locks those decisions.

---

## HOW TO READ THIS DOCUMENT

- §85 locks the **approach decision** — quoting as universal mechanism, hyphenation blessed, phrase spans rejected.
- §86 specifies the **lexer changes** — quote-state accumulation, unclosed-quote error, punctuation handling inside quotes.
- §87 specifies **where `QUOTED_STRING` tokens are valid** — value positions only, not names or field names.
- §88 locks **literal display via `show`** — a `QUOTED_STRING` in `show` target position displays the literal text. Partially resolves U6 from the v1 gap inventory.
- §89 locks **quoted reserved words as data values** — `QUOTED_STRING` tokens bypass the v1c §46 vocabulary exclusion.
- §90 locks the **canonical rendering rule** — the renderer quotes values only when necessary (multi-word or reserved-word values).
- §91 locks **case normalization inside quotes** — quoted strings are lowercased, consistent with the rest of the language.
- §92 locks **empty quotes rejected** — `""` is a parse error.
- §93 updates the vocabulary table. **No new reserved words.** Still 31.
- §94 adds test sentences 69–80 to the test suite (extending from v2b §83's sentence 68).
- §95 extends the build boundary (v2b §84).

---

### §85 — D7 RESOLUTION: QUOTING WITH HYPHENATION BLESSED

**Decision: Multi-word string values are expressed using double-quote delimiters. Hyphenation remains the encouraged convention for names, field names, and simple category values. Multi-word phrase spans (lexer phrase registry) are not adopted. LOCKED as D7 resolution. Supersedes v1d §61 (single-token strings) and resolves the v2a §72 deferral.**

Three approaches were evaluated in the D7 checkpoint analysis:

| Approach | Outcome |
|---|---|
| **A — Quoting** | **Adopted.** Mechanically clean. Self-delimiting — no domain-pack registry needed. Resolves reserved-word conflicts (§89). One new lexer state. Prose-as-syntax invariant holds with a bounded softening (quote marks are English punctuation, not programming syntax). |
| **B — Hyphenation** | **Blessed as convention.** Already works for names (`find-big-orders`), field names (`total-amount`), and simple category values (`in-progress`). Zero implementation cost. Does not handle multi-word noun phrases (`chest pain`, `Los Angeles`) or data from external systems that uses spaces. |
| **C — Phrase spans** | **Rejected.** Reserved-word collision risk (e.g., `not applicable` collides with the `not` operator; `shortness of breath` collides with the `of` connective). Round-trip property depends on runtime phrase-registry state. Per-domain-pack registry and cross-pack collision detection required. Implementation cost is high. Fails the deterministic-interpretation invariant (v1c §52) when an unregistered phrase is silently split into separate tokens. |

**Why quoting wins over phrase spans despite prose-as-syntax cost.** The prose-as-syntax invariant (v7.5g §13) says "valid inscriptions are readable as English prose." A quoted phrase is readable as English prose with a quoted term — which is a thing English does ("set the status to 'in progress'"). The softening is bounded: one syntax mark, one rule to learn ("wrap multi-word values in quotes"). Phrase spans would have preserved surface prose but introduced invisible registry-dependent behavior — a worse violation of the language's "no silent misinterpretation" principle (v1c §52) than quote marks are of the prose-as-syntax principle.

**Coexistence.** The two mechanisms coexist without ambiguity:
- `with status as in-progress` — valid, single hyphenated token, no quotes needed.
- `with status as "in progress"` — valid, quoted multi-word string.
- `with status as "not applicable"` — valid, reserved word inside quotes is data (§89).
- `with status as active` — valid, single-word bare value, unchanged from v1.

Quoting a single-word value (`with status as "active"`) is redundant but not an error (§94, sentence 78). The stored value is `active` either way. The renderer emits without quotes when the value is single-token and non-reserved (§90).

**v1d §61 is superseded.** That section locked single-token strings as a v1 constraint and noted the limitation for documentation. The constraint is now relaxed: multi-word strings are supported via quoting. Single-word bare strings continue to work exactly as before — no existing program changes behavior.

---

### §86 — LEXER: QUOTE-STATE ACCUMULATION

**Decision: The lexer gains a quote state. When it encounters an opening double-quote character, it accumulates all characters (including spaces) until the closing double-quote, then emits a single `QUOTED_STRING` token whose value is the text between the quotes. LOCKED as lexer extension.**

The whitespace-splitting rule (inception §22) is *modified, not replaced*. Outside of quotes, whitespace splitting works exactly as before. Inside quotes, whitespace is preserved as part of the token value. This is a new lexer state — the lexer tracks whether it is currently inside quotes.

**Processing order.** The quote-state check happens *before* whitespace splitting. The lexer scans the input line character by character. When it encounters `"`, it enters quote-state and accumulates characters until the next `"`. The accumulated content (without the quote characters) is lowercased (§91) and emitted as a `QUOTED_STRING` token. Characters outside quotes are processed by the existing whitespace-splitting, punctuation-stripping, and vocabulary-lookup pipeline unchanged.

**Unclosed quotes.** If a line ends without a closing quote, the lexer produces a parse error (Outcome 4, v1c §50):

> *"I see an opening quote mark but no closing one on this line. Each quoted phrase needs both opening and closing marks."*

Quotes do not span lines. This preserves the one-statement-per-line rule (inception §22, whitespace normalization). Each line is a complete statement; a quoted phrase that spans lines would break that invariant.

**Punctuation inside quotes.** Commas, periods, question marks, and exclamation marks inside quotes are *preserved* — they are part of the string value, not decorative. Outside quotes, decorative punctuation stripping (inception §22) continues unchanged. `with text as "Hello, world!"` stores the value `hello, world!` (lowercased per §91, punctuation preserved).

**Escaped quotes.** Not supported in v2c. A quoted string cannot contain a literal double-quote character. This is acceptable for the v1/v2 target domains — business categories, healthcare terms, and compliance labels do not contain quote marks. If this limitation surfaces in practice, backslash escaping (`\"`) could be added in a future version without changing the quoting mechanism's architecture.

**Multiple quoted strings on one line.** A single line may contain more than one quoted string: `remember an order called o1 with status as "in progress" and label as "high priority"`. The lexer enters and exits quote-state for each pair of quotes independently. The tokens emitted are: ... QUOTED_STRING("in progress") AND UNKNOWN("label") AS QUOTED_STRING("high priority").

---

### §87 — PARSER: `QUOTED_STRING` IN VALUE POSITIONS

**Decision: A `QUOTED_STRING` token is valid anywhere the parser expects a value — after `with` (bare value position), after `as` in a `with...as` clause, and after an operator in a `where` clause. `QUOTED_STRING` is NOT valid in name positions or field-name positions. LOCKED as parser token-acceptance rule.**

The parser treats `QUOTED_STRING` exactly like `UNKNOWN` for slot-filling purposes in value positions: it fills the same slots, produces the same AST node types, and flows through the same semantic checks. The only difference is that the token's value may contain spaces.

**Value positions where `QUOTED_STRING` is accepted:**

| Position | Example | AST effect |
|---|---|---|
| After `with` (bare, no `as`) — list construction | `with "hello world" and "goodbye"` | Value node with multi-word string |
| After `as` in `with...as` — field value | `with status as "in progress"` | Field value node with multi-word string |
| After operator in `where` — comparison value | `where status is "in progress"` | Condition value node with multi-word string |
| After `from` in `gather...from...to` — range bound | `gather the nums from "start" to "end"` | Range bound (though numeric ranges are the common case) |

**Positions where `QUOTED_STRING` is NOT accepted:**

| Position | Example | Error |
|---|---|---|
| After `called` — variable name | `remember a list called "my list"` | *"Names can't have spaces. Try a hyphenated name like 'my-list' instead."* |
| After `how to` — composition name | `remember how to "find big": ...` | *"Composition names can't have spaces. Try a hyphenated name like 'find-big' instead."* |
| Before `as` in `with...as` — field name | `with "total amount" as 75` | *"Field names can't have spaces. Try a hyphenated name like 'total-amount' instead."* |
| Before operator in `where` — field reference | `where "field name" is above 50` | *"Field names can't have spaces. Try a hyphenated name like 'field-name' instead."* |
| Before `of` — field reference in field access | `show "total amount" of order1` | *"Field names can't have spaces. Try 'show total-amount of order1' instead."* |
| In multi-field `each...show` — field name | `each the orders show "total amount" and status` | *"Field names can't have spaces. Try a hyphenated name like 'total-amount' instead."* |

The error messages consistently guide toward hyphenation, which is the blessed convention for multi-word names and field names (§85).

**`and` disambiguation is unchanged.** The four `and` context rules (inception §21) and the fifth rule (v2a §69) all disambiguate by looking *forward* — checking what comes after `and`. A `QUOTED_STRING` appearing *before* `and` (as a value just consumed) does not affect disambiguation. `with status as "in progress" and priority as high` works: the parser consumes `"in progress"` as the value for `status`, sees `and`, looks ahead to `priority` followed by `as`, and correctly identifies field continuation.

---

### §88 — LITERAL DISPLAY: `show` WITH QUOTED STRINGS

**Decision: When `show`'s target is a `QUOTED_STRING` token, the interpreter displays the literal text content of the quoted string. This is distinct from name-lookup (`show <UNKNOWN>`, which looks up a symbol) and field-access (`show <UNKNOWN> of <UNKNOWN>`, which accesses a record field). LOCKED as `show` extension. Partially resolves U6 from the v1 dogfooding gap inventory.**

The gap (v1 gap inventory U6): "No simple way to display a small heading or label between sections of output." The note said this was tied to D7. With quoting, it is resolved:

```
show "Section A: counts before filtering"
count the orders
show "Section B: counts after filtering"
filter the orders where total is above 50
count the orders
```

→ Line 1 displays: `Section A: counts before filtering`
→ Line 3 displays: `Section B: counts after filtering`

**Why this interpretation is unambiguous.** `show` currently expects either an UNKNOWN token (name lookup) or an UNKNOWN followed by `of` (field access). A `QUOTED_STRING` in target position cannot be a name lookup — names are single tokens, never quoted (§87). It cannot be a field access — `show <QUOTED_STRING> of <name>` is an error because field names can't be quoted (§87). The only remaining interpretation is: display this literal text. No existing behavior changes; this is a new capability for a new token type.

**`show "X"` vs `show X`.** These are different operations:
- `show orders` — look up the symbol `orders` in the symbol table, display its value.
- `show "orders"` — display the literal text `orders`.

The distinction is explicit and consistent with the quoting mechanism's core principle: quotes mark content as data, not as a reference.

**Auto-show.** Literal display via `show` is always explicit — the user writes `show "text"`. There is no auto-show for literal strings. This is consistent: auto-show applies to verb results (`count`, `combine`, `keep`), not to `show` itself.

---

### §89 — QUOTED RESERVED WORDS AS DATA VALUES

**Decision: A `QUOTED_STRING` token bypasses vocabulary lookup entirely. The lexer produces `QUOTED_STRING` based on the quote delimiters, without checking the content against the reserved-word list. A quoted reserved word in a value position is valid data. LOCKED as vocabulary-exclusion extension.**

This modifies the scope of v1c §46. That section locked: "A vocabulary word appearing where the parser expects UNKNOWN or NUMBER is a parse error." The modification: this rule applies to *unquoted* tokens only. `QUOTED_STRING` tokens are never checked against the vocabulary table — their content is always treated as data.

**Examples:**
- `with label as "filter"` — stores the string `filter` as the value of the `label` field. The VERB `filter` is not invoked.
- `with category as "not applicable"` — stores the string `not applicable`. The OPERATOR `not` is not invoked.
- `with tag as "and"` — stores the string `and`. The CONNECTIVE `and` is not invoked.

**Why this is correct.** The whole purpose of quoting is to disambiguate data from syntax. If quotes do not override vocabulary classification, they are incomplete — they handle multi-word values but not single-word collisions, which is the less important of the two problems. A compliance domain might need categories named after operations. A labeling system might use `"count"` or `"combine"` as status labels. The quoting mechanism must handle these cases to be useful.

**Unquoted vocabulary words remain errors.** `with label as filter` (no quotes) still produces the v1c §46 error: *"The word 'filter' is a verb in Inscript and can't be used as a value. Try a different word, or wrap it in quotes: with label as \"filter\"."* The error message is extended from v1c §46's wording to suggest the quoting fix.

---

### §90 — CANONICAL RENDERING: CONDITIONAL QUOTING

**Decision: The renderer emits quotes around string values when — and only when — the value is multi-word (contains a space) or matches a reserved word. Single-word non-reserved values are rendered without quotes. LOCKED as rendering rule.**

The rule is mechanically deterministic. The renderer checks each string value: does it contain a space, or does it match any entry in the reserved-word table (v2a §73, 31 words)? If yes, emit with quotes. If no, emit bare.

**Examples:**

| Stored value | Renderer output | Reason |
|---|---|---|
| `active` | `with status as active` | Single-word, not reserved. |
| `in progress` | `with status as "in progress"` | Multi-word. |
| `filter` | `with label as "filter"` | Single-word but reserved (VERB). |
| `not applicable` | `with category as "not applicable"` | Multi-word (also contains a reserved word, but multi-word is sufficient). |
| `75` | `with total as 75` | Number, not a string — rendered without quotes per existing rules. |

**Round-trip property holds.** Parsing the renderer's output produces the same AST:
- `with status as active` → UNKNOWN("active") → same as original.
- `with status as "in progress"` → QUOTED_STRING("in progress") → same value.
- `with label as "filter"` → QUOTED_STRING("filter") → data value, not VERB — same as original.

Without conditional quoting, `with label as filter` (renderer omitting quotes on a reserved-word value) would re-parse as a VERB token, breaking the round-trip. The "quote reserved words" half of the rule exists specifically to preserve round-trip integrity.

---

### §91 — CASE NORMALIZATION INSIDE QUOTES

**Decision: The lexer lowercases the content of quoted strings, consistent with the language's universal case normalization. `"In Progress"` and `"in progress"` produce the same stored value: `in progress`. LOCKED as case-normalization extension.**

The inception checkpoint §22 locks: "The lexer lowercases all input before vocabulary lookup." v1d §57 locks: "All symbol table names are stored in lowercase." The language has no case-sensitive construct. Quoted strings follow the same rule.

If quoted strings preserved case, they would be the first and only case-sensitive construct in the language. `where status is "In Progress"` would fail to match data stored as `"in progress"` — a silent mismatch with no indication of why. Two programs that look identical to a non-programmer would behave differently based on capitalization, violating deterministic interpretation (v1c §52) in spirit.

Case-sensitive strings are a real need for some domains (proper nouns, external identifiers, codes). That need belongs alongside the broader type system work (Q8 from inception §25) — not bolted onto quoting as a side effect. When a future version adds case-sensitive string support, it would do so with explicit syntax (e.g., a case-preserving string type) rather than relying on quote marks that currently carry no case semantics.

---

### §92 — EMPTY QUOTES REJECTED

**Decision: `""` (a pair of quote marks with nothing between them) is a parse error. LOCKED as empty-quote rejection.**

Error message: *"There's nothing between these quote marks. If you want to store a value, put it between the quotes."*

An empty string has no meaning in the v1/v2 target domains. The language has no string operations (concatenation, emptiness checks, interpolation) that would give an empty value a purpose. `where status is ""` would mean "where status equals nothing" — a missing-value question that belongs to a future null/optional-value design, not to the quoting mechanism.

If a future version adds string operations and richer type semantics, empty strings could become meaningful and this restriction could be relaxed. For now, empty quotes are a typo, and the error message treats them that way.

---

### §93 — VOCABULARY TABLE (UNCHANGED)

No vocabulary changes in v2c. The table from v2a §73 / v2b §82 remains current:

| Category | Words | Count |
|---|---|---|
| **Verbs** | `remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each` | 8 |
| **Connectives** | `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`, `of` | 10 |
| **Operators** | `is`, `above`, `below`, `not` (single-word) | 4 |
| **Multi-word operator component** | `equal` (combines with `to` per inception §22) | 1 |
| **Articles** | `the`, `a`, `an` | 3 |
| **v2 deferred verbs** | `transform`, `choose`, `compare` | 3 |
| **v2 deferred connectives** | `when`, `unless` | 2 |
| **Total reserved** | | **31** |

Quoting is a lexer mechanism, not vocabulary. No reserved words are added or removed. The double-quote character is a lexer delimiter (like the colon, inception §22), not a vocabulary word.

---

### §94 — NEW TEST SENTENCES

Extending the test suite from sentence 68 (v2b §83) to sentence 80.

**Sentence 69 — Basic multi-word string value**
```
remember an order called o1 with status as "in progress"
show o1
```
→ `status: in progress`
**Tests:** §86 — quoted multi-word value stored correctly. Display omits quotes (values are data, quotes are syntax).

**Sentence 70 — Multi-word string in a where clause**
```
remember an order called o1 with status as "in progress"
remember an order called o2 with status as shipped
remember a list called orders with o1 and o2
keep the orders where status is "in progress"
```
→ Line 4 auto-shows: `status: in progress` (one match)
**Tests:** §87 — `QUOTED_STRING` accepted after operator in `where` clause. String equality comparison works with multi-word values.

**Sentence 71 — Reserved word inside quotes**
```
remember a category called c1 with label as "not applicable"
show label of c1
```
→ `not applicable`
**Tests:** §89 — `not` inside quotes is data, not an operator. Vocabulary exclusion bypassed.

**Sentence 72 — Mixed single-word and multi-word values in one record**
```
remember a task called t1 with status as "in progress" and priority as high
show t1
```
→ `status: in progress, priority: high`
**Tests:** §87 — multi-word and single-word values coexist. `and` correctly separates the `status` field (quoted value) from the `priority` field (bare value).

**Sentence 73 — Quoted field name in `of` is an error**
```
remember a metric called m1 with pressure as 120
show "blood pressure" of m1
```
⚠ Outcome 4: *"Field names can't have spaces. Try 'show blood-pressure of m1' instead."*
**Tests:** §87 — `QUOTED_STRING` in field-name position before `of` is rejected with hyphenation guidance.

**Sentence 74 — Hyphenated and quoted values are different strings**
```
remember a task called t1 with status as in-progress
remember a task called t2 with status as "in progress"
show status of t1
show status of t2
```
→ Line 3: `in-progress`
→ Line 4: `in progress`
**Tests:** §85 — `in-progress` (one token, hyphenated) and `in progress` (quoted, contains space) are different stored values. The two mechanisms coexist; the user's choice is preserved.

**Sentence 75 — Unclosed quote error**
```
remember a note called n1 with text as "hello world
```
⚠ Outcome 4: *"I see an opening quote mark but no closing one on this line. Each quoted phrase needs both opening and closing marks."*
**Tests:** §86 — unclosed quotes produce a clear error.

**Sentence 76 — Empty quotes error**
```
remember a note called n1 with text as ""
```
⚠ Outcome 4: *"There's nothing between these quote marks. If you want to store a value, put it between the quotes."*
**Tests:** §92 — empty quotes rejected.

**Sentence 77 — Literal display via show**
```
show "Section A: before filtering"
remember a list called nums with 10 and 20 and 30
count the nums
show "Section B: done"
```
→ Line 1: `Section A: before filtering`
→ Line 3: `3`
→ Line 4: `Section B: done`
**Tests:** §88 — `show` with `QUOTED_STRING` displays literal text. Punctuation inside quotes (colon) preserved. Interleaved with normal operations.

**Sentence 78 — Quoted single word is redundant but valid**
```
remember a task called t1 with status as "active"
remember a task called t2 with status as active
show status of t1
show status of t2
```
→ Line 3: `active`
→ Line 4: `active`
**Tests:** §85 — quoting a single word is redundant but not an error. Stored value is identical. Renderer emits both without quotes (both are single-word, non-reserved).

**Sentence 79 — Reserved word value renders with quotes (round-trip)**
```
remember a tag called t1 with label as "filter"
show t1
```
→ `label: filter`
⊕ Canonical rendering of line 1: `remember a tag called t1 with label as "filter"` (renderer quotes `filter` because it is a reserved word — §90). Re-parsing the rendered form produces the same AST.
**Tests:** §90 — conditional quoting for reserved-word values preserves round-trip integrity.

**Sentence 80 — Quoted name is an error**
```
remember a list called "my list" with 1 and 2 and 3
```
⚠ Outcome 4: *"Names can't have spaces. Try a hyphenated name like 'my-list' instead."*
**Tests:** §87 — `QUOTED_STRING` in name position after `called` is rejected with hyphenation guidance.

---

### §95 — UPDATED BUILD BOUNDARY (extension to v2b §84)

The v2b build boundary is extended (not replaced):

| Component | v2c additions |
|---|---|
| **Lexer** | Quote-state accumulation (§86). Character-by-character scan for `"` before whitespace splitting. Accumulate until closing `"`. Lowercase content. Emit `QUOTED_STRING` token. Unclosed-quote error (Outcome 4). Punctuation preserved inside quotes. Multiple quoted strings per line supported. |
| **Parser** | Accept `QUOTED_STRING` in value positions: after `with` (bare), after `as`, after operators in `where` (§87). Reject `QUOTED_STRING` in name positions (after `called`, after `how to`) and field-name positions (before `as`, before operators in `where`, before `of`, in multi-field `each...show`) with hyphenation-guiding error messages (§87). Accept `QUOTED_STRING` as `show` target for literal display (§88). Reject empty quotes (§92). |
| **Semantic analyzer** | `QUOTED_STRING` tokens bypass vocabulary exclusion (§89). No other semantic-analyzer changes — `QUOTED_STRING` values flow through the same type-checking, schema-homogeneity, and field-existence checks as `UNKNOWN` values. |
| **Interpreter** | `show` with `QUOTED_STRING` target: display the literal text, no symbol-table lookup (§88). All other value positions: `QUOTED_STRING` values are stored and compared identically to `UNKNOWN` values. |
| **Canonical renderer** | Conditional quoting (§90): emit quotes when the value is multi-word (contains space) or matches a reserved word. Single-word non-reserved values remain bare. |
| **Result interface** | Unchanged. Five outcomes per v1c §50. New errors (unclosed quotes, empty quotes, quoted names/fields) map to Outcome 4 (parse error). |
| **CLI wrapper** | Unchanged. |

**What v2c does NOT build:**

- Case-sensitive strings (future type-system work, Q8).
- Escape characters inside quotes (future if needed).
- Multi-word field names or composition names (§87 — names stay single-token, hyphenation blessed).
- `transform` / `choose` / `compare` (still v2-deferred per inception §25).
- `when` / `unless` and event-driven execution (still v2-deferred).
- Composition parameters and `from` chaining (still v2-deferred per v1b §41 / Q9).
- Nested records and chained `of` (v2b §77 sub-decision I).
- Tile interface, proposal engine, domain packs (Branch C/E).

---

## WHAT IS LOCKED

This addendum locks:

- **Quoting as universal multi-word string mechanism (§85).** Double-quote delimiters in value positions. Hyphenation blessed as convention for names and field names. Phrase spans (lexer phrase registry) rejected. Supersedes v1d §61. Resolves v2a §72 deferral.
- **Lexer quote-state (§86).** Character-by-character scan for `"`. Accumulate until closing `"`. Lowercase content. Preserve punctuation inside quotes. Unclosed-quote error. No line-spanning. No escape characters.
- **`QUOTED_STRING` in value positions only (§87).** Accepted after `with`, after `as`, after operators in `where`. Rejected in name positions and field-name positions with hyphenation-guiding errors.
- **Literal display via `show` (§88).** `show "text"` displays the literal text. Distinct from name-lookup and field-access. Partially resolves U6 (multi-word headings/labels).
- **Quoted reserved words as data (§89).** `QUOTED_STRING` bypasses vocabulary lookup. `"filter"`, `"not applicable"`, `"and"` are valid data values. Extends v1c §46 scope to unquoted tokens only. Error message for unquoted reserved words updated to suggest quoting.
- **Conditional rendering (§90).** Renderer quotes multi-word values and reserved-word values. Single-word non-reserved values remain bare. Round-trip property preserved.
- **Case normalization inside quotes (§91).** Quoted strings lowercased, consistent with universal case normalization. Case-sensitive strings deferred to type-system work (Q8).
- **Empty quotes rejected (§92).** `""` is a parse error. Empty-string semantics deferred to future null/optional-value design.
- **No vocabulary changes (§93).** 8 verbs, 10 connectives, 31 reserved words — unchanged from v2a/v2b.
- **Twelve new test sentences (§94).** Sentences 69–80 extending the test suite from 68.

This addendum does NOT modify any prior locked decision except v1d §61, which is explicitly superseded (relaxed, not contradicted — single-word bare strings still work exactly as before). Specifically:
- `filter` remains destructive (v1d §66 / inception §24).
- `keep` remains non-destructive (v2a §67).
- `combine` remains numeric-only and non-destructive (v1b §38, §39).
- Copy semantics unchanged (inception §24).
- The `of` connective (v2a §68, generalized in v2b §77) is unchanged — field references remain single UNKNOWN tokens.
- The fifth `and` rule (v2a §69) is unchanged — field names in multi-field `show` remain single UNKNOWN tokens.
- Composition return values (v2b §76) unchanged.
- Stepwise execution (v1d §56) unchanged.
- The five-outcome taxonomy (v1c §50) unchanged.
- The reorderer's v1 scope (v1d §55) unchanged.

---

## RESUME PROMPT (Inscript Programming Language v2c)

*We are resuming from the Inscript Programming Language Multi-Word Strings Addendum v2c (May 12, 2026), which extends v2b Composition Returns (May 12, 2026), and back through v2a/v1d/v1c/v1b/v1a and the Inception Checkpoint v1 (all May 11–12, 2026). v2c resolves D7 — the single biggest open design question deferred through v2a §72. **The approach is quoting**: double-quote delimiters for multi-word string values in value positions. Hyphenation is blessed as the convention for names and field names. Phrase spans (lexer phrase registry) were rejected — reserved-word collision risk, registry-dependent round-trip fragility, and per-domain-pack configuration cost were all too high. **Eight decisions locked**: (1) Lexer quote-state accumulation — character-by-character scan, accumulate between quotes, lowercase content, preserve punctuation, unclosed-quote error, no line-spanning, no escapes. (2) `QUOTED_STRING` accepted in value positions (after `with`, after `as`, after operators in `where`), rejected in name and field-name positions with hyphenation-guiding errors. (3) Literal display via `show "text"` — partially resolves U6. (4) Quoted reserved words bypass v1c §46 vocabulary exclusion — `"filter"`, `"not applicable"` are valid data. (5) Conditional rendering — quotes emitted only for multi-word or reserved-word values. (6) Case normalization inside quotes — lowercased, consistent with language-wide rule. (7) Empty quotes rejected. (8) No vocabulary changes — still 31 reserved words. **v1d §61 (single-token strings) is superseded** — multi-word strings now supported. All other locked decisions unchanged. Twelve new test sentences (69–80). Build specification is now eight documents: inception checkpoint v1, addenda v1a/v1b/v1c/v1d/v2a/v2b/v2c, plus the 80-sentence test suite. Quote marks are the first (and only) piece of syntax in the language. The cost is one rule to learn; the benefit is universal — any multi-word value, any domain, no registry configuration.*

---

## PROVENANCE NOTE

This addendum was verified against:

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026):
  - §10 (concept-layer vocabulary) — quoting names what the user is doing ("this phrase is data") without machine-facing syntax.
  - §17 (verb signatures, slot filling) — `show` target slot extended to accept `QUOTED_STRING` for literal display (§88). All other verb signatures unchanged.
  - §19 (vocabulary scaling, domain packs) — quoting decouples domain vocabulary from lexer state. Domain packs require no phrase registry. The base mechanism stays small (§85).
  - §20 (word salad test) — quoted phrases pass: a non-programmer reads `"in progress"` as "the phrase in progress."
  - §22 (lexer specification) — whitespace splitting modified (not replaced) by quote-state (§86). Case normalization extended to quoted content (§91). Decorative punctuation stripping does not apply inside quotes (§86). Valid name characters unchanged — names remain single tokens with letters, digits, and hyphens (§87).
  - §24 (auto-show, interpreter behaviors) — `show` literal display (§88) is a new behavior, not a modification of auto-show. Auto-show applies to verb results, not to `show` itself.
  - §25 (v1/v2 deferral table) — Q8 (type system) referenced for case-sensitivity deferral (§91).
- **`inscript_addendum_v1a_pre_build.md`** (May 11, 2026):
  - §29 (reserved word list, exclusion rule) — the reserved-word list defines which single-word values trigger conditional quoting in the renderer (§90). The exclusion rule is scoped to unquoted tokens (§89).
  - §33 (canonical prose rendering) — extended by conditional quoting rule (§90).
- **`inscript_addendum_v1b_design_resolutions.md`** (May 11, 2026):
  - §41 (composition call syntax) — composition names stay single-token (§87). No change.
  - §43 (`from` disambiguation) — `QUOTED_STRING` in value position after `from` in `remember...from <verb phrase>` is handled by the existing recursive-descent path. No change to disambiguation.
  - §44 (complete disambiguation ruleset) — unchanged. `QUOTED_STRING` does not add a new disambiguation case because it is accepted only in positions where `UNKNOWN` was already accepted.
- **`inscript_addendum_v1c_implementation_hardening.md`** (May 11, 2026):
  - §46 (vocabulary words cannot be string values) — scope modified: applies to unquoted tokens only (§89). Error message extended to suggest quoting.
  - §50 (five-outcome taxonomy) — new errors (unclosed quotes, empty quotes, quoted names/fields) map to Outcome 4. No new outcome categories.
  - §51 (parser lookahead) — unchanged. Quote-state is a lexer mechanism, not parser lookahead.
  - §52 (deterministic interpretation only) — the deciding principle against phrase spans (§85). Quoting preserves determinism; phrase spans would have violated it.
- **`inscript_addendum_v1d_build_boundary.md`** (May 11, 2026):
  - §55 (reorderer scope) — unchanged. Quoted strings in value positions are reordered the same as bare values.
  - §57 (case normalization) — extended to quoted string content (§91).
  - §61 (single-token strings) — **superseded** by §85. The constraint is relaxed; single-word bare strings still work.
  - §65 (test sentences 35–48) — extended in v2a §74 to 59, v2b §83 to 68, now §94 to 80.
  - §66 (build boundary) — extended through v2a §75, v2b §84, now §95.
- **`inscript_addendum_v2a_dogfooding_resolutions.md`** (May 12, 2026):
  - §67 (`keep` verb) — `keep` with quoted values in `where` clauses (test sentence 70). No change to `keep` semantics.
  - §68 (`of` connective) — field references remain single UNKNOWN tokens. `show "X" of Y` is an error (§87). The §68 forward-compatibility note ("D7 will extend what constitutes a valid field reference") is resolved: D7 does not extend field references because field names stay single-token (architect decision M).
  - §69 (fifth `and` rule) — field names in multi-field `show` remain single UNKNOWN tokens. `QUOTED_STRING` in field-name position is rejected (§87). No change to the fifth `and` rule.
  - §71 (descriptor preservation) — unchanged. Descriptors are UNKNOWN tokens at parse time, not value positions.
  - §72 (D7 deferral) — **resolved** by this addendum. The deferral is closed.
  - §73 (vocabulary table) — unchanged in §93.
  - §74 (test sentences 49–59) — extended in v2b §83 to 68, now §94 to 80.
  - §75 (build boundary) — extended in v2b §84, now §95.
- **`inscript_addendum_v2b_composition_returns.md`** (May 12, 2026):
  - §76 (composition return values) — unchanged. Compositions returning quoted values flow through the same value path.
  - §77 (generalized `of`) — field references remain single UNKNOWN tokens. No change.
  - §82 (vocabulary table) — unchanged in §93.
  - §83 (test sentences 60–68) — extended in §94 to 80.
  - §84 (build boundary) — extended in §95.
- **`inscript_checkpoint_v2c_multi_word_strings.md`** (May 12, 2026):
  - The D7 checkpoint analysis evaluated three approaches against every locked spec surface. The architect approved the recommended approach (quoting + hyphenation blessed) and all sub-decisions (L–R). This addendum locks those decisions.
- **`inscript_gap_inventory_2026_05_12_v1_dogfooding.md`** (May 12, 2026):
  - D7 (single-token strings preclude domain-natural language) — resolved by §85.
  - U6 (no multi-word headings/labels) — partially resolved by §88 (`show "text"` literal display).
- **`mobius_paradigm_checkpoint_v7_5g_inscript_resolution.md`**: §13 (prose-as-syntax invariant) — the invariant holds with a bounded softening. Quote marks are English punctuation, not programming syntax. The language now contains one syntactic mark; it is the same mark English uses to delimit special terms.
- **External review:** Not solicited for this addendum. The D7 checkpoint analysis recommended external review before locking. The architect chose to proceed directly to the locking addendum. External review can still be solicited post-lock if stress-testing surfaces issues; any findings would produce a v2c.1-patch or v2d addendum, not a rollback.
- **Filename:** `inscript_addendum_v2c_multi_word_strings.md` — domain `inscript` (provisional, pre-vault), class `addendum`, version `v2c` (third in the v2 series, following v2a/v2b), subtitle `multi_word_strings`.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE MULTI-WORD STRINGS ADDENDUM v2c*

*May 12, 2026*

*The language that reads as English prose now holds data that has spaces in it.*
*One syntax mark — the first the language has ever needed — and the only one it may ever need.*
*Quote marks cost one rule to learn: "wrap multi-word values in quotes."*
*They resolve the reserved-word collision that v1c §46 created.*
*They scale to every domain pack without a single line of registry configuration.*
*The clarity budget absorbs the cost because the cost is bounded and the benefit is universal.*

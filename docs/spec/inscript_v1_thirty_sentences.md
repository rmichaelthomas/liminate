# INSCRIPT PROGRAMMING LANGUAGE v1
## The Thirty Sentences — Test Specification

**Date:** May 11, 2026
**Purpose:** Pre-code deliverable per `inscript_addendum_v1a_pre_build.md` §35. Every sentence uses only v1 vocabulary (§11). Each sentence is a test case for the lexer, parser, semantic analyzer, and interpreter. Design questions surfaced by the sentences are collected at the end — these require architect decisions before the build begins.

**Vocabulary constraint:** 7 verbs (`remember`, `show`, `filter`, `count`, `gather`, `combine`, `each`), 9 connectives (`where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`), 5 operators (`is`, `above`, `below`, `equal to`, `not`), 2 articles (`the`, `a`/`an`), 1 delimiter (`:`).

**Notation:** Each sentence specifies expected interpreter behavior. State carries forward within a program. "→" indicates displayed output. "⊕" indicates a symbol table side effect (stored but not displayed). "⚠" indicates an expected error.

---

## Program 1 — Basic Values and Lists

**Tests:** `remember` (flat value, flat list), `show`, `count` (auto-show on standalone expression).

**Sentence 1**
```
remember a number called age with 30
```
⊕ Symbol table: `age` = 30 (number). No output.
**Tests:** `remember` simplest form. `called` introduces name. `with` introduces value. Type inferred from value. The word `number` between `a` and `called` is a prose descriptor, not a type keyword — see DQ1.

**Sentence 2**
```
remember a list called colors with red and blue and green
```
⊕ Symbol table: `colors` = ["red", "blue", "green"] (list of strings). No output.
**Tests:** `and` inside a `with` clause as list construction (§21 context rule 1: parser state = `with` clause, next token = value/unknown). Type inferred: multiple values joined by `and` → list.

**Sentence 3**
```
show age
```
→ `30`
**Tests:** `show` simplest form. Displays value of named item from symbol table.

**Sentence 4**
```
show colors
```
→ `red, blue, green` (display format — see DQ7)
**Tests:** `show` on a list. Display format for lists is a design question.

**Sentence 5**
```
count the colors
```
→ `3`
**Tests:** `count` as standalone expression triggers auto-show (§24). `count` on a list returns the number of items.

---

## Program 2 — Structured Records

**Tests:** `remember` with `as` connective for structured records (§23), `each` as iteration verb, `show` inside `each`.

**Sentence 6**
```
remember an order called order1 with total as 75 and status as active
```
⊕ Symbol table: `order1` = {total: 75, status: "active"} (record). No output.
**Tests:** `as` connective for field assignment. `and` inside a `with...as` clause as record field continuation (§21 context rule 4). Type inference: `75` → number, `active` → string. Record schema stored in symbol table (§23).

**Sentence 7**
```
remember an order called order2 with total as 30 and status as active
```
⊕ Symbol table: `order2` = {total: 30, status: "active"} (record). No output.
**Tests:** Second record with same schema as `order1`.

**Sentence 8**
```
remember an order called order3 with total as 120 and status as pending
```
⊕ Symbol table: `order3` = {total: 120, status: "pending"} (record). No output.
**Tests:** Third record, different `status` value.

**Sentence 9**
```
remember a list called orders with order1 and order2 and order3
```
⊕ Symbol table: `orders` = [order1, order2, order3] (list of records). No output.
**Tests:** List construction where items are named records (not literals). Copy semantics (§24): `orders` contains copies of the records, not references.

**Sentence 10**
```
each the orders show total
```
→ `75`
→ `30`
→ `120`
**Tests:** `each` as iteration verb (§17 signature: collection + action). Sub-operation is `show total` — display the `total` field of each item. `each` produces output because its sub-operation (`show`) produces output (§24). See DQ2 for `each` dual role.

---

## Program 3 — Filtering Records

**Tests:** `filter` on record fields (field-based condition), `is` as equality operator, in-place modification (§24), `count`, `each` second usage.

*State entering Program 3: assumes Program 2 has been executed. `orders` = [{total: 75, status: active}, {total: 30, status: active}, {total: 120, status: pending}].*

**Sentence 11**
```
filter the orders where total is above 50
```
⊕ `orders` modified in-place to [{total: 75, status: active}, {total: 120, status: pending}]. No output.
**Tests:** `filter` with field-based condition. `where` introduces condition. `total` is a field reference — parser classifies this unknown word as a field reference because it's inside a `where` clause before an operator (§22). `is above` is a comparison (§21: `is` followed by known operator → comparison introducer). In-place modification: `order2` is removed from `orders` (§24).

**Sentence 12**
```
show orders
```
→ Displays the two remaining orders (display format — see DQ7).
**Tests:** Confirms `filter` modified `orders` in-place.

**Sentence 13**
```
filter the orders where status is active
```
⊕ `orders` modified in-place to [{total: 75, status: active}]. No output.
**Tests:** `is` as equality operator (§21: `is` followed by a value/name, not a known operator → `is` is the equality operator itself). After filtering: `order3` (status: pending) is removed. Only `order1` remains.

**Sentence 14**
```
count the orders
```
→ `1`
**Tests:** `count` confirms the in-place filter chain reduced `orders` to one item.

**Sentence 15**
```
each the orders show status
```
→ `active`
**Tests:** `each` with field access on a filtered collection. Confirms only one order remains and its status is `active`.

---

## Program 4 — Number Operations

**Tests:** `gather` (range generation, auto-show, implicit naming), `filter` with `each` pronoun, `count`, `combine` (auto-show, non-destructive), `remember...from` (capturing verb phrase output).

**Sentence 16**
```
gather the numbers from 1 to 10
```
→ `1, 2, 3, 4, 5, 6, 7, 8, 9, 10` (see DQ5 for auto-show question)
⊕ Symbol table: `numbers` = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] (list of numbers).
**Tests:** `gather` creates a range. `from` and `to` as range connectives. Name `numbers` parsed from the noun after the article (§24). `gather` both stores AND displays — see DQ5.

**Sentence 17**
```
filter the numbers where each is above 5
```
⊕ `numbers` modified in-place to [6, 7, 8, 9, 10]. No output.
**Tests:** `each` inside a `where` clause functions as a self-reference pronoun meaning "the current item being tested" — NOT as the iteration verb. See DQ2. `is above` is a comparison. In-place modification.

**Sentence 18**
```
count the numbers
```
→ `5`
**Tests:** `count` confirms filter reduced list from 10 to 5 items.

**Sentence 19**
```
combine the numbers
```
→ `40`
**Tests:** `combine` on a list of numbers produces their sum (6+7+8+9+10 = 40). Auto-show as standalone expression. `combine` does NOT modify the source list — see DQ4.

**Sentence 20**
```
remember the result called total from combine the numbers
```
⊕ Symbol table: `total` = 40 (number). No output.
**Tests:** `from` takes a verb phrase as its argument — the parser must recursively parse `combine the numbers` as a sub-expression whose return value fills the `value` slot of `remember` (see DQ8). `remember` produces no output. `combine` is re-executed (idempotent on unmodified source).

---

## Program 5 — The `not` Operator

**Tests:** `not above` (≤), `not below` (≥), `not equal to` (≠). Each has distinct semantics from its non-negated form (§21).

**Sentence 21**
```
gather the scores from 1 to 10
```
⊕ Symbol table: `scores` = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].
**Tests:** Second `gather` usage.

**Sentence 22**
```
filter the scores where each is not above 7
```
⊕ `scores` modified in-place to [1, 2, 3, 4, 5, 6, 7]. No output.
**Tests:** `not above 7` means ≤ 7 (includes the boundary value 7). This is distinct from `below 7`, which would be < 7 (excludes 7). Per §21: "`not above 50` = ≤ 50, not `below 50` = < 50."

**Sentence 23**
```
filter the scores where each is not below 3
```
⊕ `scores` modified in-place to [3, 4, 5, 6, 7]. No output.
**Tests:** `not below 3` means ≥ 3 (includes the boundary value 3). Applied to already-filtered list [1..7], removes 1 and 2.

**Sentence 24**
```
filter the scores where each is not equal to 5
```
⊕ `scores` modified in-place to [3, 4, 6, 7]. No output.
**Tests:** `not equal to` as the negation of the multi-word `equal to` operator. `not` modifies `equal to` the same way it modifies `above` and `below`. Removes the single item matching 5.

---

## Named Compositions

**Tests:** `remember how to` (named composition definition, §19 Mechanism 3), named composition as reusable verb phrase, definition-time grammar validation vs. call-time name resolution (§23).

*These are standalone definitions, not part of a sequential program. They test the definition mechanism, not execution.*

**Sentence 25**
```
remember how to find-big-orders: filter the orders where total is above 50
```
⊕ Symbol table: `find-big-orders` = named composition (stored verb phrase). No output.
**Tests:** `how` signals named composition definition (§11). `to` precedes the composition name. `:` is the delimiter separating name from body (§22). Body is parsed for grammar validity at definition time but names (`orders`, `total`) are NOT resolved against the symbol table — they are resolved at call time (§23). Hyphenated name `find-big-orders` is valid (§22: names may contain letters, digits, and hyphens).

**Sentence 26**
```
remember how to count-active: filter the orders where status is active and count the orders
```
⊕ Symbol table: `count-active` = named composition (stored verb phrase). No output.
**Tests:** Named composition body containing `and` as operation sequencing (§21 context rule 3: after a complete verb phrase, next word is a verb → operation sequencing). The body is two operations: filter + count. Grammar validated at definition time.

---

## Compound Conditions

**Tests:** `and`/`or` inside `where` clauses creating compound condition nodes (§21). These are standalone sentences operating on hypothetical data — they test the parser, not the interpreter.

*Assume `orders` exists as defined in Program 2 (pre-filter state): [{total: 75, status: active}, {total: 30, status: active}, {total: 120, status: pending}].*

**Sentence 27**
```
filter the orders where total is above 50 and status is active
```
⊕ `orders` modified in-place. Keeps items where BOTH conditions are true. Result: [{total: 75, status: active}].
**Tests:** `and` inside a `where` clause before a field reference → compound condition (§21 context rule 2). AST: `and` node with two sub-conditions: `total > 50` and `status == active`. Both must be true.

**Sentence 28**
```
filter the orders where total is below 30 or status is pending
```
⊕ `orders` modified in-place. Keeps items where EITHER condition is true. Result depends on prior state.
**Tests:** `or` inside a `where` clause before a field reference → compound condition. AST: `or` node with two sub-conditions. Either may be true.

---

## Mixed Precedence — Amber Light

**Tests:** Mixed `and`/`or` in a single `where` clause triggers disambiguation prompt (§30).

**Sentence 29**
```
filter the orders where total is above 50 and status is active or status is pending
```
⚠ Amber Light: "I'll read this as: (total is above 50 AND status is active) OR status is pending. Is that what you mean? If not, split it into two statements."
**Tests:** `and` binds tighter than `or` (§21: tree has `or` at root, `and(condition1, condition2)` as left child, `condition3` as right child). Parser succeeds deterministically but the mixed-precedence rule (§30) fires the Amber Light before execution. User must confirm or restructure.

---

## The `equal to` Operator

**Tests:** `equal to` as explicit equality, multi-word token handling (§22).

**Sentence 30**
```
filter the orders where total is equal to 75
```
⊕ `orders` modified in-place. Keeps items where `total` equals exactly 75.
**Tests:** `equal to` as a multi-word operator. Lexer combines `equal` + `to` into a single `equal_to` token via one-word lookahead (§22). `is equal to` is a comparison: `is` introduces comparison, `equal to` is the operator. Distinct from `is 75` (where `is` is itself the equality operator) — both produce the same result but via different parse paths.

---

## Error Case — Reserved Word Violation

**Tests:** Reserved word exclusion rule (v1a §29).

**Sentence 31**
```
remember a value called filter with 10
```
⚠ Error: "The word 'filter' is reserved in Inscript — it's used as a verb. Please choose a different name."
**Tests:** `filter` is in the reserved word list (v1a §29). The lexer tags `filter` as a verb. The parser, expecting a name after `called`, encounters a verb token and produces the reserved-word error rather than a generic parse failure.

---

## Coverage Summary

| Requirement (per v1a §35) | Sentences | Status |
|---|---|---|
| Every verb at least twice, simple + complex | All 7 verbs appear ≥2× | ✓ |
| ≥3 sentences with structured records (`as`) | 6, 7, 8 | ✓ |
| ≥2 named compositions (`remember how to`) | 25, 26 | ✓ |
| ≥2 compound conditions (`and`/`or` in `where`) | 27, 28 | ✓ |
| ≥1 mixed-precedence Amber Light | 29 | ✓ |
| ≥1 reserved word violation (error path) | 31 | ✓ |
| ≥1 multi-statement program | Programs 1–5 | ✓ |

| Verb | Appearances | Sentences |
|---|---|---|
| `remember` | 11 | 1, 2, 6, 7, 8, 9, 20, 25, 26, 31 + sentence 30 data setup |
| `show` | 5 | 3, 4, 12 + inside `each` at 10, 15 |
| `filter` | 10 | 11, 13, 17, 22, 23, 24, 27, 28, 29, 30 |
| `count` | 3 | 5, 14, 18 |
| `gather` | 2 | 16, 21 |
| `combine` | 2 | 19, 20 |
| `each` | 3 | 10, 15 (as verb) + 17, 22, 23, 24 (as pronoun in `where`) |

| Operator | Tested in sentences |
|---|---|
| `is` (comparison introducer) | 11, 17, 22, 23, 24, 27, 28, 29, 30 |
| `is` (equality operator) | 13, 27, 28, 29 |
| `above` | 11, 17, 27, 29 |
| `below` | 23, 28 |
| `equal to` | 24, 30 |
| `not above` | 22 |
| `not below` | 23 |
| `not equal to` | 24 |

| `and`/`or` context rule (§21) | Tested in sentences |
|---|---|
| List construction (`with` clause) | 2, 9 |
| Compound condition (`where` clause) | 27, 28, 29 |
| Operation sequencing (verb + verb) | 26 |
| Record field continuation (`with...as`) | 6, 7, 8 |

---

## Design Questions Surfaced

These questions were discovered by writing the sentences. Each requires an architect decision before the corresponding build stage begins. They are numbered DQ1–DQ8 for reference.

**DQ1 — Prose descriptors between article and `called`.**
In `remember a number called age with 30`, the word `number` appears between the article `a` and the connective `called`. It is not in the vocabulary table — the lexer tags it as `unknown`. The parser must decide what to do with it. Two options: (a) ignore it as decorative prose (like articles), or (b) treat it as an optional type hint and validate against the inferred type. Since types are inferred from values (§23) and no explicit type annotations are required for v1, option (a) is consistent with locked decisions. **Recommendation:** The parser ignores unknown words between an article and `called`. They are prose scaffolding that makes the sentence read naturally but carry no semantic weight. This means `remember a called age with 30` and `remember a number called age with 30` and `remember a thing called age with 30` all produce the same result.
*Surfaces in:* sentences 1, 2, 6, 7, 8, 9.

**DQ2 — `each` as verb vs. `each` as pronoun in `where` clauses.**
The word `each` has two roles. As a verb (sentence 10: `each the orders show total`), it means "iterate over the collection and perform the action on each item." As a word inside a `where` clause (sentence 17: `filter the numbers where each is above 5`), it means "the current item being tested" — a self-reference pronoun. The lexer tags `each` as a verb in both cases. The parser must disambiguate by context: if `each` appears inside a `where` clause (parser state = condition parsing), it is a pronoun referring to the current item. If `each` appears in verb position (start of sentence or after operation-sequencing `and`), it is the iteration verb. **Recommendation:** The parser tracks clause context. Inside a `where` clause, `each` is reclassified from verb to self-reference pronoun. This is analogous to `and`/`or` having four meanings based on parser state (§21) — `each` has two meanings based on parser state.
*Surfaces in:* sentence 10 (verb), sentence 17 (pronoun), sentences 22–24 (pronoun).

**DQ3 — `combine` semantics per type.**
The `combine` verb (§17 signature: targets) produces a single value from a collection. What operation does it perform for different types? **Recommendation:** For v1, `combine` operates on lists of numbers only (sum). `combine` on a list of strings or records produces a type error: "I can only combine numbers. [name] contains [type]." String concatenation and record merging are v2 considerations. This keeps `combine` simple and unambiguous for the v1 beachhead (business rules, data filtering, numeric analysis).
*Surfaces in:* sentences 19, 20.

**DQ4 — `combine` does not modify the source.**
Only `filter` is locked as in-place modification (§24). `combine` produces a scalar (sum) from a collection. **Recommendation:** `combine` returns a new value and does NOT modify the source collection. After `combine the numbers`, `numbers` is still the original list. The sum is a new value — auto-shown if standalone, captured via `remember...from` if named. This is confirmed by the sentence sequence: sentence 19 (`combine the numbers` → 40) followed by sentence 20 (`remember the result called total from combine the numbers` → re-executes combine on the unchanged list, stores 40).
*Surfaces in:* sentences 19, 20.

**DQ5 — `gather` auto-show behavior.**
§24 states auto-show applies to `gather` "(when not creating a named collection)." §24 also locks that `gather` always creates a named collection. This creates an apparent contradiction: if `gather` always names its result, and auto-show applies only when it doesn't name its result, then `gather` never auto-shows. **Recommendation:** `gather` both stores AND auto-shows. The parenthetical in §24 was written before the "inline naming" behavior was locked, and the two decisions interact. A non-programmer who says `gather the numbers from 1 to 10` expects to see the numbers. Silence would feel broken. `gather` is the one verb where both the side effect (storing) and the display (showing) happen unconditionally.
*Surfaces in:* sentence 16.

**DQ6 — Named composition call syntax.**
Sentences 25 and 26 define named compositions. How are they called? The inception checkpoint §19 shows `find-big-orders from find-loyal-customers` — a composition name used as a standalone statement. But the parser's first step is "find the verb" (§17). In a standalone `find-big-orders`, there is no vocabulary verb. **Recommendation:** Named compositions are added to the symbol table with type `composition`. When the parser cannot find a vocabulary verb, it checks whether the first unknown word is a named composition. If so, it retrieves the stored verb phrase and parses it as the statement's operation. This is a parser fallback, not a new verb — the composition name effectively becomes a user-defined verb. `from` after a composition name introduces a data source override: `find-big-orders from the new-data` means "run the find-big-orders verb phrase against `new-data` instead of the default target."
*Surfaces in:* sentences 25, 26 (definitions only — call syntax is a pre-build decision, not tested in these sentences because the interpreter isn't built yet).

**DQ7 — Display format.**
How does `show` render different types? **Recommendation for v1:** Numbers display as-is (`30`, `3.14`). Strings display as-is without quotes (`active`, `portland`). Lists display as comma-separated values (`red, blue, green` or `75, 30, 120`). Records display as field: value pairs (`total: 75, status: active`). Lists of records display one record per line. `each...show [field]` displays one value per line. These are v1 defaults; a formatting system is a v2 consideration.
*Surfaces in:* sentences 3, 4, 10, 12, 15.

**DQ8 — `from` taking a verb phrase argument.**
In sentence 20 (`remember the result called total from combine the numbers`), the `from` connective introduces a verb phrase (`combine the numbers`), not a name or range. The parser must recognize that `from` in a `remember` statement can take a sub-expression as its argument, recursively parsing the remainder as a complete verb phrase whose return value fills the value slot. **Recommendation:** The parser, when processing `from` inside a `remember` statement, checks whether the next token is a verb. If so, it recursively parses a complete verb phrase and uses its return value. If the next token is a name, it resolves normally. This is the same recursive descent mechanism used for `each` (§21: "`each` wraps sub-operations via recursive descent").
*Surfaces in:* sentence 20.

---

## Note on Sentence Count

The specification in v1a §35 calls for "thirty sentences." This document contains thirty-one: thirty that test correct behavior plus one that tests the reserved word error path (sentence 31). The error sentence is numbered 31 rather than included in the count of thirty to preserve the convention that "the thirty sentences" refers to valid programs. The error case is an additional test case, not a replacement.

---

*These sentences are the language made concrete. Every ambiguity they surface is an ambiguity the lexer, parser, or interpreter would have to resolve silently — and silent resolution is what this language exists to prevent.*

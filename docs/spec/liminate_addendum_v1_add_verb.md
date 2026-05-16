# ADDENDUM
## Liminate Programming Language — `add` Verb
### v1 — Dynamic List Growth

**Status:** LOCKED — EXTENDS the Inscript Programming Language chain (Inception Checkpoint v1 through Addendum v4a, May 11–13, 2026)
**Date:** May 16, 2026
**Author:** Rob Thomas / R. Michael Thomas (architect) and Claude (analytical partner)
**Document type:** Addendum — adds one verb (`add`) to the base vocabulary, resolves nine design questions (AV-Q1 through AV-Q9), defines 12 test sentences, locks the verb specification. Does not modify any prior locked decision.
**Domain prefix:** `liminate` (provisional, pre-vault — third document in the `liminate_*` chain)
**Relationship to prior checkpoints:** Extends `inscript_addendum_v4a_pack_verbs_and_port.md` (May 13, 2026) as the language specification chain endpoint. Downstream of `liminate_inception_checkpoint_v1_session_contracts_and_semantic_continuity.md` (May 16, 2026), which identified the gap: Liminate can shrink lists (`filter`, `keep`) but cannot grow them, and composition cannot simulate list growth. Downstream of `liminate_checkpoint_v1_branch_g_distribution_and_release.md` (May 15, 2026) for verified repo state. Section numbering is independent of the Inscript chain's § sequence and independent of the other `liminate_*` documents.

> *"Add the new order to the orders."*
> *A non-programmer reads that and knows exactly what it does.*

---

## HOW TO READ THIS DOCUMENT

- §1–§7 resolve design questions AV-Q1 through AV-Q7 (one per section), each with a locked decision and rationale.
- §8 resolves AV-Q9 (word collision check — taken before AV-Q8 because it gates the reserved-word decision).
- §9 provides the updated vocabulary table.
- §10 specifies the verb's implementation shape: AST node, parser, analyzer, interpreter, renderer.
- §11 resolves AV-Q8 with 12 test sentences (sentences 128–139, continuing from the 127-sentence test suite locked in v4a).
- **WHAT IS LOCKED** / **WHAT IS NOT LOCKED** collect decisions.
- The resume prompt closes the document.
- The BUILD follows this addendum. No implementation was performed during this design session.

---

## Part I — Design Resolutions

### §1 — AV-Q1: `add` BELONGS IN THE BASE VOCABULARY

**Decision: `add` is a base verb. It is not a pack verb. The base verb count goes from 10 to 11. The total reserved word count goes from 34 to 35. LOCKED as v1 verb addition.**

Three factors made this decision structural rather than preferential:

1. **Every domain needs it.** Business rules accumulate orders. Healthcare accumulates patient events. Session contracts accumulate verified facts. Smart home logs accumulate readings. No domain pack can claim `add` as contextually specific — it is universally required.

2. **Composition cannot simulate it.** This is the gap that surfaced this verb. No combination of existing verbs appends an item to an existing list (Session Contracts Inception Checkpoint v1, §19–§22). The only workaround — re-remembering the entire list with all items re-specified — is unworkable for reactive programs where state grows over time.

3. **The pack verb alternative has worse properties.** The pack verb contract (v4a §137) currently supports only the `set_value` execution type. `add` would need a new `append_to_list` execution type, requiring resolution of open question V4-Q1 before `add` could ship. The pack approach would produce identical surface syntax (`add X to Y`) but require a loaded pack to work — an unnecessary dependency for a universal operation.

**Word salad test (Inception Checkpoint §20).** "Add the new order to the orders." A non-programmer reads that and immediately understands it. Pass.

**Precedent.** `keep` was added to the base vocabulary in v2a §67. `choose` was promoted from deferred to active in v2d §99. `finish` was added in v3a §112. Each addition was locked in its own addendum with design rationale, and each passed the word salad test. `add` follows the same pattern.

---

### §2 — AV-Q2: VERB SIGNATURE

**Decision: The verb signature is `["item", "target"]`. The parser shape is `add [article]? <item-value> to [article]? <list-name>`. The `to` connective separates the item from the target. LOCKED as v1 verb signature.**

**Slot signature** (extending Inception Checkpoint §17 / v2a §73):

| Slot | Connective | Required | What it holds |
|---|---|---|---|
| `item` | (none — positional, before `to`) | Yes | The value being added |
| `target` | `to` | Yes | The list receiving the item |

**Connective reuse.** `to` already exists as a connective (used by `gather` for range endpoints). Verb-first dispatch resolves the ambiguity: if the verb is `add`, `to` means "target list"; if the verb is `gather`, `to` means "range end." This is the same disambiguation pattern the parser uses throughout.

**Article consumption.** Consistent with existing verbs (`filter`, `keep`, `count`, `combine`, `each`), articles before both the item and the target are optional and decorative. All four forms are valid:

```
add new-order to orders
add the new-order to orders
add new-order to the orders
add the new-order to the orders
```

**Item slot accepts:** `UNKNOWN` tokens (bare words — resolved against the symbol table as name references, or treated as string literals if unknown), `NUMBER` tokens (numeric literals), and `QUOTED_STRING` tokens (v2c §86 quoted literals). These are the same value types accepted by `remember ... with` for list items, parsed via the existing `_parse_value` path.

**Target slot accepts:** `UNKNOWN` tokens only. The target must be a name referencing an existing list in the symbol table. Reserved words, numbers, and quoted strings are rejected with appropriate error messages.

**Inline record construction is not supported.** `add a order with total as 75 to the orders` is not valid. To add a record, `remember` it first, then `add` it. This matches how list construction works today — `remember a list called orders with order1 and order2` references pre-existing names.

---

### §3 — AV-Q3: TYPE COMPATIBILITY RULES

**Decision: Type compatibility for `add` follows the existing v1d §59 list homogeneity rule. Same-category types are allowed; cross-category additions are rejected with a clear error. Record schema differences within a list of records are allowed. LOCKED as v1 type compatibility.**

The analyzer enforces list homogeneity at construction time (`_check_remember_list` in analyzer.py). The same rule applies at `add` time — adding an item whose type category does not match the list's type category is a semantic error.

| List type | Item type | Result |
|---|---|---|
| `list_of_numbers` | number | Allowed |
| `list_of_strings` | string | Allowed |
| `list_of_records` | record | Allowed (regardless of schema) |
| `list_of_numbers` | string | Error |
| `list_of_strings` | number | Error |
| `list_of_records` | number or string | Error |
| `list_of_numbers` or `list_of_strings` | record | Error |

**Error message pattern:** "'<list>' is a list of <type>. '<item>' is <other-type> and can't be added to it."

**Mixed-schema records.** Liminate lists of records already allow records with different field sets. The schema-mismatch mechanism in the analyzer catches field-access issues downstream (when `filter`, `keep`, `show`, or `each` reference a field that doesn't exist on all records). `add` does not introduce a new schema-enforcement point — it follows the existing construction-time behavior.

---

### §4 — AV-Q4: IN-PLACE MUTATION

**Decision: `add` mutates the target list in place, like `filter`. The item is deep-copied into the list. LOCKED as v1 mutation semantics.**

The existing mutation model has two clear precedents:

- `filter` is in-place: `entry.value[:] = kept` — the list in the symbol table is mutated directly.
- `keep` is non-destructive: a new list is built via `copy.deepcopy`; the source is untouched.

"Add the new order to the orders" unambiguously implies mutation in plain English. The whole point of `add` is that the target list grows. A non-destructive `add` would defeat its purpose — the downstream use case (session contracts accumulating state in `when` action blocks) requires the list to actually change.

**Copy semantics for the item.** The item being added is deep-copied into the list, consistent with Liminate's copy-on-store semantics (Inception Checkpoint §24, implemented in `_store`). If the user adds a record reference to a list, then later modifies the original record, the copy in the list is unaffected.

---

### §5 — AV-Q5: NO AUTO-SHOW

**Decision: `add` produces no output. It is a silent mutation, like `filter` and `remember`. LOCKED as v1 output behavior.**

The pattern across existing verbs: verbs that produce a new value auto-show (`keep`, `count`, `gather`, `combine`); verbs that mutate existing state are silent (`filter`, `remember`). `add` is a mutation verb — it modifies an existing list without producing a new value.

Auto-showing after every `add` would also be noisy in accumulation loops. A `when` handler that fires 50 times and adds an item each time should not produce 50 lines of output showing the growing list.

If the user wants to see the result, the idiomatic pattern is sequencing: `add the new-order to the orders and show the orders` or `add the new-order to the orders and count the orders`.

---

### §6 — AV-Q6: CONTEXT ALLOWANCES

**Decision: `add` is allowed in all five execution contexts. Inside `each` bodies, an analyzer-level guard prevents adding to the same list being iterated. LOCKED as v1 context rules.**

| Context | Allowed | Notes |
|---|---|---|
| Sequential programs (Phase 1) | Yes | Basic case |
| `when` action blocks (Phase 2) | Yes | Primary use case — list accumulation in response to events |
| `choose` branches | Yes | Conditional addition |
| Composition bodies | Yes | Reusable accumulation patterns |
| `each` bodies | Yes, with guard | Cannot add to the list being iterated |

**Why `add` inside `each` is allowed but `filter`/`keep` inside `each` is not.** `filter` and `keep` are whole-list operations — "filter this entire list." Inside `each`, you're operating item-by-item. The conceptual mismatch ("for each item, filter the whole list") is confusing and was explicitly rejected in v2d §102.

`add` is a single-item operation. "For each order, add its total to the running tally" is a clear, natural accumulation pattern. The operation makes conceptual sense per-item — as long as you're not modifying the list you're walking.

**Self-mutation guard.** The analyzer checks whether the `add` target is the same list being iterated in the enclosing `each`. If so, it rejects the operation:

Error message: "'<list>' is the list being iterated — you can't add to it while iterating. Try adding to a different list."

This is an analyzer-level check, not a parser-level ban. The distinction from `filter`/`keep`'s blanket parser ban reflects the different reasoning: `filter`/`keep` are conceptually wrong inside `each`; `add` is conceptually right but technically unsafe when self-referential.

---

### §7 — AV-Q7: LIVE VALUE RESTRICTION

**Decision: `add` on a live-value list is rejected in all contexts, same restriction as `filter`. LOCKED as v1 live-value rule.**

Live values are adapter-owned (v3a §111). The adapter is the source of truth — it pushes updates into the symbol table. If user code mutates a live value via `add`, the adapter and the user are fighting over the same state. This is the same structural problem as `filter` on live values, just in the opposite direction: `filter` shrinks adapter data; `add` grows adapter data. Both corrupt the adapter's ownership model.

Error message: "'<name>' is a live value provided by the domain pack. 'add' modifies the list and can't be used on it — the domain pack controls this value."

**The user's alternative:** Maintain a separate user-owned list and add to that. The user reads from the adapter's live value and writes to their own list:

```
remember a list called my-events with placeholder
when new-event is not equal to none:
    add the new-event to my-events
```

Here `new-event` might be a live value, but `my-events` is user-owned. Clean ownership boundary.

**Relationship to existing restrictions:**

| Verb | Live-value behavior | Reasoning |
|---|---|---|
| `filter` | Rejected in all contexts | Destructive — corrupts adapter data |
| `add` | Rejected in all contexts | Destructive — corrupts adapter data |
| `keep` | Allowed in all contexts | Non-destructive — reads without modifying |
| `remember` | Rejected in action blocks only | Phase 1 provides initial value; Phase 2 adapter owns it |

---

### §8 — AV-Q9: NO WORD COLLISION

**Decision: The word `add` does not collide with any existing reserved word, variable name, field name, or string value in the repo. It is safe to reserve. LOCKED as v1 collision check.**

Verified against:

- **vocabulary.py (sha 1fa4830):** `add` is not in VERBS, CONNECTIVES, OPERATORS, ARTICLES, V2_RESERVED, or MULTI_WORD_RESERVED.
- **Eight representative example `.limn` programs** across all feature generations (program2_orders, dogfood_v2d_params_and_branching, dogfood_v3a_event_driven, dogfood_v3a_game, dogfood_v3a_healthcare, dogfood_v3a_smart_home, dogfood_8_v2a_features, dogfood_navigate_test): `add` does not appear as a variable name, field name, or string value.
- **test_vocabulary.py (sha f70a5ac):** No reference to `add` as a test fixture or expected value.

Variable naming conventions across the repo use domain-specific names (`order1`, `score`, `level`, `readings`, `patient`, `light-level`, `occupancy`). `add` as a user-chosen name would be unusual in any of these domains.

---

## Part II — Specification

### §9 — UPDATED VOCABULARY TABLE

Updated from v3a §124 / v4a §137 (unchanged at 34).

| Category | Words | Count |
|---|---|---|
| **Verbs** | `remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each`, `choose`, `finish`, `add` | **11** |
| **Connectives** | `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`, `of`, `if`, `otherwise`, `when`, `unless` | 14 |
| **Operators** | `is`, `above`, `below`, `not` (single-word) | 4 |
| **Multi-word operator component** | `equal` (combines with `to` per Inception Checkpoint §22) | 1 |
| **Articles** | `the`, `a`, `an` | 3 |
| **V2 deferred verbs** | `transform`, `compare` | 2 |
| **Total reserved** | | **35** |

Delta from v3a §124: +1 verb (`add`). Reserved word count was 34; now 35.

**No words were removed.** All prior reserved words remain reserved.

**Verb signatures** (extending Inception Checkpoint §17 / v2a §73 / v2d §104 / v3a §124):

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
| `choose` | condition, consequence, alternative |
| `finish` | (none) |
| `add` | item, target |

---

### §10 — IMPLEMENTATION SPECIFICATION

This section specifies the implementation shape for `add` across all pipeline stages. The build follows this specification.

**AST node.**

```python
@dataclass
class AddNode(ASTNode):
    item: ASTNode    # The value being added (NumberLiteral, BareWord, NameRef, QuotedString, FieldAccessNode)
    target: NameRef  # The list receiving the item
```

**Parser.** `_parse_add` is called when the verb token is `add`. Shape:

1. Consume optional article (`_consume_optional_article`).
2. Parse item value via `_parse_value(stream)` — accepts UNKNOWN, NUMBER, QUOTED_STRING, and `<field> of <record>` field-access expressions.
3. Consume `to` connective. If missing: error — "'add' needs a target list — try: add <item> to <list-name>."
4. Consume optional article.
5. Consume target name via `_consume_target(stream, verb="add")` — UNKNOWN only.
6. Return `AddNode(item=<parsed-item>, target=<parsed-target>)`.

Add `"add"` to the verb dispatch in `_parse_verb_statement`. Add `"add": ["item", "target"]` to `VERB_SIGNATURES`.

**Analyzer.** `_check_add` validates:

1. **Target exists and is a list.** Reuse `_require_list(name, symtab, verb="add")`. Error message for non-list: "I can only add to a list. '<name>' is <type>."
2. **Type compatibility.** Infer the item's type category. Compare against the list's type category. Cross-category mismatch: "'<list>' is a list of <type>. '<item>' is <other-type> and can't be added to it."
3. **Item validation.** If the item is a NameRef, verify it exists in the symbol table. If it's a FieldAccessNode, run `_check_field_access`. If BareWord, NumberLiteral, or QuotedString — trivially valid.
4. **Self-mutation guard (each context).** If the analyzer is running inside an `each` clause context and the target name matches the iterated collection name: "'<list>' is the list being iterated — you can't add to it while iterating. Try adding to a different list."
5. **Live-value restriction.** If the target name is in `live_value_names`: "'<name>' is a live value provided by the domain pack. 'add' modifies the list and can't be used on it — the domain pack controls this value."

**Interpreter.** `_exec_add`:

```python
def _exec_add(node: AddNode, symtab, current_item):
    entry = symtab[node.target.name]
    item_value = _evaluate_expression(node.item, symtab, current_item)
    entry.value.append(copy.deepcopy(item_value))
    # Update the symbol-table entry's type if needed (e.g., first add to
    # a list that was empty after filtering).
    return []  # no output — silent mutation
```

The list in the symbol table is mutated directly via `append`. The item is deep-copied. No output is returned.

**Renderer.** `render(AddNode)` produces the canonical form: `add <item> to <list-name>`. Articles are not preserved in canonical rendering (consistent with existing verbs — the canonical form is the minimal form).

**Lexer.** `add` is added to the `VERBS` frozenset. The lexer tags it as `TokenType.VERB`. No new token types are needed.

**Reorderer.** `add` parses in canonical order (verb-first). The reorderer places the verb token at position 0 per the existing verb-first rule. No new reorderer logic is required — the item and `to` connective follow the verb naturally.

---

## Part III — Test Sentences

### §11 — TEST SENTENCES

Extending the test suite from sentence 127 (v4a) to sentence 139.

**Sentence 128 — `add` basic: record to list of records**
```
remember an order called o1 with total as 75 and status as active
remember an order called o2 with total as 30 and status as pending
remember a list called orders with o1
add o2 to the orders
count the orders
```
→ Line 5: `2`
**Tests:** §1 (base verb), §2 (signature), §4 (in-place — count reflects the addition).

**Sentence 129 — `add` basic: number to list of numbers**
```
remember a list called scores with 10 and 20
add 30 to scores
show scores
```
→ Line 3: `10, 20, 30`
**Tests:** §2 (number item), §4 (in-place — show reflects appended item).

**Sentence 130 — `add` basic: string to list of strings**
```
remember a list called names with alice and bob
add charlie to the names
show names
```
→ Line 3: `alice, bob, charlie`
**Tests:** §2 (bare-word string item), §4 (in-place).

**Sentence 131 — `add` type mismatch: number to list of strings**
```
remember a list called words with hello and world
add 42 to words
```
⚠ Error: "'words' is a list of text. '42' is a number and can't be added to it."
**Tests:** §3 (type compatibility — cross-category rejection).

**Sentence 132 — `add` type mismatch: string to list of numbers**
```
remember a list called values with 1 and 2 and 3
add oops to values
```
⚠ Error: "'values' is a list of numbers. 'oops' is text and can't be added to it."
**Tests:** §3 (reverse type mismatch).

**Sentence 133 — `add` to a non-list target**
```
remember a value called total with 100
add 5 to total
```
⚠ Error: "I can only add to a list. 'total' is a number."
**Tests:** §10 (analyzer — target must be a list).

**Sentence 134 — `add` inside `each`: accumulation pattern**
```
remember an order called o1 with total as 75
remember an order called o2 with total as 30
remember an order called o3 with total as 120
remember a list called orders with o1 and o2 and o3
remember a list called big-totals with 0
each the orders add total to big-totals
show big-totals
```
→ Line 7: `0, 75, 30, 120`
**Tests:** §6 (`each` body — adding to a different list). Note: `total` resolves against the current iterator item's field via v1c §49 iterator-first resolution; the resolved number is added to `big-totals`.

**Sentence 135 — `add` inside `each`: self-mutation guard**
```
remember a list called items with 1 and 2 and 3
each the items add 99 to items
```
⚠ Error: "'items' is the list being iterated — you can't add to it while iterating. Try adding to a different list."
**Tests:** §6 (self-mutation guard).

**Sentence 136 — `add` inside `choose` branch**
```
remember a value called level with 75
remember a list called alerts with none
choose if level is above 50: add level to the alerts
show alerts
```
→ Line 4: `none, 75`
**Tests:** §6 (`choose` context).

**Sentence 137 — `add` mixed-schema record to list of records**
```
remember an order called o1 with total as 75 and status as active
remember an item called item1 with name as widget and price as 10
remember a list called things with o1
add item1 to things
count things
```
→ Line 5: `2`
**Tests:** §3 (mixed-schema records allowed — different field sets coexist in the list).

**Sentence 138 — `add` with articles in both positions**
```
remember a list called numbers with 1 and 2
add the 3 to the numbers
show numbers
```
→ Line 3: `1, 2, 3`
**Tests:** §2 (article consumption — both positions optional and decorative).

**Sentence 139 — reserved word: `add` cannot be used as a name**
```
remember a value called add with 5
```
⚠ Error: "The word 'add' is reserved in Liminate — it's used as a verb. Please choose a different name."
**Tests:** §8 (reserved word enforcement per v1a §29).

---

## WHAT IS LOCKED

This addendum locks:

- **`add` as a base verb** (§1). Verb count: 11 (was 10). Total reserved words: 35 (was 34).
- **Verb signature** `["item", "target"]` with parser shape `add [article]? <item-value> to [article]? <list-name>` (§2).
- **Type compatibility** follows v1d §59 homogeneity; cross-category additions rejected; mixed-schema records allowed (§3).
- **In-place mutation** with deep-copy of item, like `filter` (§4).
- **No auto-show** — silent mutation, like `filter` and `remember` (§5).
- **Context allowances** — all five contexts permitted; `each` body has analyzer-level self-mutation guard (§6).
- **Live-value restriction** — `add` on adapter-owned lists rejected in all contexts, like `filter` (§7).
- **No word collision** (§8).
- **Updated vocabulary table** at 35 reserved words (§9).
- **Implementation specification** — AST node, parser, analyzer, interpreter, renderer (§10).
- **Twelve test sentences** (128–139) covering happy paths, type mismatches, non-list target, `each` accumulation, self-mutation guard, `choose` branch, mixed-schema records, article consumption, and reserved-word enforcement (§11).

## WHAT IS NOT LOCKED

- **The build itself.** This addendum specifies; the implementation follows in a separate session.
- **`add` inside `when` action blocks.** §6 allows this, and the specification supports it, but no test sentence exercises the `when` context because `when` handlers require a domain pack with adapter-driven events to test end-to-end. A `when`-context test sentence should be added when the session contract pack (Session Contracts Inception Checkpoint, Phase 2) is built.
- **Live-value restriction test coverage.** §7's restriction is tested via unit tests against the analyzer, not via a test sentence, because it requires a domain pack with declared live values. Coverage should be added alongside the existing live-value unit tests in `test_analyzer.py`.
- **Open question V4-Q1** (additional pack verb execution types beyond `set_value`). This addendum does not resolve V4-Q1 and does not depend on its resolution.
- **Any change to any prior locked decision.** Every decision in this addendum is additive.

---

## RESUME PROMPT (Liminate `add` Verb v1)

*We are resuming from the Liminate `add` Verb Addendum v1 (May 16, 2026), which extends the Inscript Programming Language specification chain (Inception Checkpoint v1 through Addendum v4a, May 11–13, 2026) with a new base verb. This is the third `liminate_*` document in the chain, produced after the Session Contracts and Semantic Continuity Inception Checkpoint v1 (same date), which identified the gap: Liminate can shrink lists but cannot grow them.*

*The addendum resolves nine design questions (AV-Q1 through AV-Q9) and locks the verb specification:*

*`add` is a base verb (verb count 11, reserved words 35). Signature: `["item", "target"]`. Parser shape: `add [article]? <item-value> to [article]? <list-name>`. The `to` connective separates item from target. Items accept UNKNOWN/NUMBER/QUOTED_STRING/FieldAccessNode. Target accepts UNKNOWN only (must reference an existing list). Type compatibility follows v1d §59 — same-category allowed, cross-category rejected, mixed-schema records allowed. In-place mutation with deep-copy (like `filter`). No auto-show (like `filter` and `remember`). Allowed in all five contexts (sequential, `when` action blocks, `choose` branches, composition bodies, `each` bodies). Inside `each`, an analyzer-level guard prevents adding to the same list being iterated. On live-value lists, `add` is rejected in all contexts (like `filter`). No word collision found.*

*Implementation specification covers AST node (`AddNode` with `item` and `target`), parser (`_parse_add` dispatched from `_parse_verb_statement`), analyzer (`_check_add` with five validation checks), interpreter (`_exec_add` — `entry.value.append(copy.deepcopy(item_value))`, returns `[]`), renderer (canonical: `add <item> to <list-name>`), lexer (`add` added to `VERBS` frozenset), reorderer (no changes — canonical order). Twelve test sentences (128–139) cover happy paths, type mismatches, non-list target, `each` accumulation, self-mutation guard, `choose` branch, mixed-schema records, article consumption, and reserved-word enforcement.*

*The build follows this addendum. Failure modes to guard during the build: (A) project knowledge as authoritative instead of repo (scan `vocabulary.py` before modifying it); (B) not reading this addendum's §10 specification before writing code; (C) modifying any test sentence's expected output without re-deriving it from the specification. The build touches: `vocabulary.py` (+1 verb, +1 signature, count assertions), `lexer.py` (no change — lexer reads from `VERBS`), `reorderer.py` (no change), `parser.py` (+`AddNode` AST, +`_parse_add`, +dispatch entry), `analyzer.py` (+`_check_add` with five checks), `interpreter.py` (+`_exec_add`), `renderer.py` (+`AddNode` case), `test_vocabulary.py` (count assertions updated to 11/35), plus new test files for the 12 sentences.*

*Build specification is now the Inscript chain (Inception Checkpoint v1 through Addendum v4a) plus this addendum — thirteen documents plus the 139-sentence test suite. 35-word base vocabulary. The base vocabulary is still sacred.*

---

## PROVENANCE NOTE

This addendum was produced from:

- **`rmichaelthomas/liminate` repo** (May 16, 2026, direct GitHub scan via vault-local MCP): `vocabulary.py` (sha 1fa4830 — 34 reserved words, 10 verbs, 14 connectives, `VERB_SIGNATURES` dict, `ALL_RESERVED` frozenset, pack verb contract), `interpreter.py` (sha 6ecb357 — `_exec_filter` in-place mutation, `_exec_keep` non-destructive copy, `_evaluate_expression`, `_exec_pack_verb`, copy-on-store via `_store`), `parser.py` (sha 9976e12 — verb dispatch, `_parse_filter_shape`, `_consume_target` with `each`-clause rejection for filter/keep, `_parse_value`, `_consume_optional_article`, `_consume_name`, pack verb parsing), `analyzer.py` (sha 0546454 — `_check_filter` with live-value rejection, `_check_keep` without live-value rejection, `_check_live_value_remember`, `_require_list`, `_check_field_access`, type inference), `test_vocabulary.py` (sha f70a5ac — count assertions at 10/14/34), eight example `.limn` programs checked for `add` collision (program2_orders sha d407b4a, dogfood_v3a_event_driven sha 458d67a, dogfood_v3a_game sha 2ae2878, dogfood_v3a_healthcare sha 5ace5af, dogfood_v3a_smart_home sha ef9cda1, dogfood_v2d_params_and_branching sha 1e19337, dogfood_8_v2a_features sha ec0403d, dogfood_navigate_test).
- **`liminate_inception_checkpoint_v1_session_contracts_and_semantic_continuity.md`** (May 16, 2026, project knowledge): Referenced for the gap identification (§19–§22 — Phase 2+ needs dynamic list accumulation), verified state table (34 reserved words, 10 verbs, 14 connectives), cross-model convergence on the downstream need.
- **`liminate_checkpoint_v1_branch_g_distribution_and_release.md`** (May 15, 2026, project knowledge): Referenced for verified repo state, failure modes carried forward (§1 — six failure modes from the rename checkpoint).
- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026, project knowledge): Referenced for vocabulary scaling architecture (§19), word salad test (§20), verb signatures (§17), interpreter behaviors (§24).
- **`inscript_addendum_v2a_dogfooding_resolutions.md`** (May 12, 2026, project knowledge): Referenced as precedent for how `keep` was added (§67 — verb addition with design rationale, signature, auto-show behavior, test sentences).
- **`inscript_addendum_v4a_pack_verbs_and_port.md`** (May 13, 2026, project knowledge): Referenced for pack verb contract (§137), `set_value` execution type, open question V4-Q1, vocabulary state at 34 reserved words (§124 via v3a).
- **`inscript_checkpoint_v1_rename_and_dsl_convergence.md`** (May 15, 2026, project knowledge): Referenced for failure mode taxonomy (§10 — Failure Modes A through E), especially Failure Mode A (project knowledge as authoritative instead of repo).
- **`liminate_add_verb_design_session_prompt.md`** (May 16, 2026, conversation): The resume prompt that opened this design session, specifying AV-Q1 through AV-Q9, failure modes to guard against, and the constraint that the build follows the addendum.
- **Conversation with architect** (May 16, 2026, this session): Nine design questions walked through individually, each explained in plain English with recommendations verified against repo source, each approved by the architect before proceeding to the next.

### NAMING VERIFICATION

Filename: `liminate_addendum_v1_add_verb.md`. Verified against the naming grammar in the rmt-working-documents skill: domain `liminate` (provisional, pre-vault), class `addendum` (versioned, closes open threads), version `v1` (first addendum in the `liminate_*` chain), subtitle `add_verb`. All separators are underscores.

---

*END OF THE LIMINATE PROGRAMMING LANGUAGE `add` VERB ADDENDUM v1*

*May 16, 2026*

*The language could always shrink a list.*
*Now it can grow one too.*
*Thirty-five words. Eleven verbs.*
*The base vocabulary is still sacred.*

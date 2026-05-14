# Inscript Programming Language

A prose-as-syntax programming language designed from the human end.

> *"Every programming language in history was designed by programmers. This one wasn't. That's why the design is different."*
> — Inscript Inception Checkpoint v1

**Status (May 13, 2026):** v1 interpreter + v2a (`keep`, `of`, multi-field `each show`, descriptor preservation) + UX polish (`--quiet`, named-offender errors, auto-show truncation) + v2.1-patches + v2b (composition return values, generalized `of`) + v2c (quoting mechanism for multi-word strings) + v2d (composition parameters with `from`, `choose` verb with `if`/`otherwise`) + v3a event-driven execution (`when`/`unless`/`finish`, two-phase listener model, single-threaded event queue, cascading triggers with cycle detection, domain-pack adapter contract) + v3b (quoted-string case preservation) + **v4a pack verb contract** (general-purpose JSON-defined pack verbs with slot signatures, type constraints, and execution dispatch; UI domain pack with 10 nouns + `navigate to <screen-name>`). **713 tests passing.** The sequential feature set (v1 → v2d), the reactive feature set (v3a/v3b), and the pack-verb extension contract (v4a) together form a structurally complete programming language; pack verbs let domains add vocabulary without touching the base 34 reserved words.

---

## Table of contents

- [What it is](#what-it-is)
- [Why it exists](#why-it-exists)
- [What makes it different](#what-makes-it-different)
- [Quick example](#quick-example)
- [Installation and running](#installation-and-running)
- [The vocabulary](#the-vocabulary)
- [The pipeline](#the-pipeline)
- [Nine outcomes](#nine-outcomes)
- [Example programs](#example-programs)
- [Current scope and deferrals](#current-scope-and-deferrals)
- [Design principles](#design-principles)
- [Project structure](#project-structure)
- [The locked test sentences](#the-locked-test-sentences)
- [Guides](#guides)
- [Specification documents](#specification-documents)
- [Lineage](#lineage)
- [Architects and builders](#architects-and-builders)
- [Status and what's next](#status-and-whats-next)

---

## What it is

`filter the orders where total is above 50` is not a prompt to an AI. It is the program.

Inscript is a general-purpose programming language whose source code is readable English prose. A bounded vocabulary of 34 words combines into sentences that execute directly. There is no separate code the prose generates — the sentence IS the program.

This is not a domain-specific language for queries or data, nor a natural-language layer over Python, nor a code-generating AI. It is a programming language with its own pipeline: lexer, reorderer, parser, semantic analyzer, interpreter. The prose-as-syntax constraint is structural, not cosmetic.

A `.insc` source file is plain text. One statement per line. Blank lines are skipped. Decorative punctuation (commas, periods, question marks, exclamation marks) is silently stripped — you can punctuate naturally.

---

## Why it exists

Programming languages are gatekeepers. They stand between human intent and computational execution, and they demand the human learn to speak the machine's language. Inscript inverts that: the machine learns to read English.

The use cases are not toys. Business rules, legal compliance, data filtering — domains where the person who understands the problem cannot currently express the solution in code. Healthcare protocols, smart home automation, narrative scripting — domains where the writer's document could BE the program. The translation step from intent to code is where errors, cost, and delay concentrate. Inscript eliminates the translation step. (See inception §13 for the v1/v2 use-case split.)

The design comes from a non-programmer. Inscript's principles were designed before the architect understood compiler pipelines. The thesis: the person affected must remain the author. A language they can't read makes them not the author.

---

## What makes it different

Five properties combine in Inscript that exist individually in other systems but never together (inception §7):

1. **Prose-as-syntax where the prose IS the executable code.** Not prose that generates code (vibe coding). Not prose that describes a game world (Inform 7, which is domain-locked). General-purpose computation expressed as readable English sentences that execute directly.

2. **Bounded vocabulary as design constraint.** 34 reserved words in the current build (10 verbs + 14 connectives + 4 single-word operators + `equal` as a multi-word component + 3 articles + 2 v2-deferred words). The vocabulary is the language boundary, not a starter set that grows. Expressiveness scales through domain packs, composition over expansion, and named-composition chunking (inception §19) — not through adding more keywords. Each v2 addition is the smallest spec change consistent with a surfaced dogfooding gap.

3. **Graduation from tiles to text within one language.** The same AST underlies a tile-composition surface (for first-encounter authoring), a prose surface (for fluent authoring), and an optional symbolic surface (for velocity). Three views, one structure. Scratch-to-Python is two languages; Inscript is one language with three surfaces. The v1 interpreter implements the prose surface; the tile surface is a separate downstream concern.

4. **Authorize, don't author.** The on-ramp is not a blank file. The system proposes a working program based on observed intent; the human modifies. First touch is on a working artifact. This requires at least one deliberate compositional act before commit — passive acceptance is not authorship. (v1a §32)

5. **Designed from liberation pedagogy.** Inscript's design principles originate in Narratia, a storytelling platform built on Paulo Freire's pedagogy of the oppressed. The principle: people must remain authors of their own narrative — including the rules that govern their systems. Every design decision is checked against that principle.

---

## Quick example

```
remember an order called order1 with total as 75 and status as active
remember an order called order2 with total as 30 and status as active
remember an order called order3 with total as 120 and status as pending
remember a list called orders with order1 and order2 and order3

filter the orders where total is above 50

each the orders show status
```

Output:

```
active
pending
```

A pure-Python equivalent would require introducing identifiers, defining a dict structure, writing a list comprehension, and using `print` calls in a for-loop. The Inscript program reads as the rule it expresses.

---

## Installation and running

Requires Python 3.10+.

```bash
git clone <repository-url>
cd inscript
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest tests/
```

Execute a file:

```bash
python -m inscript examples/program1_basics.insc
```

Start an interactive REPL (`exit` or `quit` to leave):

```bash
python -m inscript
```

Test mode (auto-confirms amber prompts so a script doesn't pause):

```bash
python -m inscript --test examples/program2_orders.insc
```

Quiet mode (suppresses the canonical-prose echo; useful for any program longer than a few lines):

```bash
python -m inscript --quiet examples/dogfood_1_corpus_summary.insc
```

Phase 2 listener mode requires at least one registered domain pack (or a program that has no adapters, in which case the listener performs initial evaluation and shuts down). The `--pack <path>` flag loads a JSON test domain pack:

```bash
python -m inscript --pack examples/dogfood_v3a_pack.json --test --quiet \
    examples/dogfood_v3a_event_driven.insc
```

Pack JSON shape:

```json
{
  "name": "monitor",
  "declarations": [["temperature", "number"]],
  "script": [
    ["temperature", 105],
    "[done]"
  ]
}
```

Multiple `--pack` flags accumulate. v3a §118 — domain pack activation via Inscript syntax (a `use`/`load` verb) is intentionally deferred; pack registration is external.

v4a §137 extends the pack JSON with optional `vocabulary` (noun additions to the reserved list while the pack is loaded) and `verbs` (slot signatures + execution dispatch). The shipped UI pack at `examples/pack_ui.json` adds 10 component nouns and the `navigate to <screen-name>` verb:

```bash
python -m inscript --pack examples/pack_ui.json --quiet \
    examples/dogfood_navigate_test.insc
```

Flags work in any argument position and can be combined. Blank source lines are mirrored to the output under `--quiet` so paragraph breaks survive.

Every statement is echoed first in canonical prose form (the parser's interpretation of what you wrote) before any output is shown — unless `--quiet` is set. This is the "Logic Preview" — see v1a §33.

---

## The vocabulary

The current base vocabulary is 34 reserved words across five categories. The complete list is the entire language surface — no other words are part of Inscript, only user-provided names and literal values. Domain packs may add their own verbs and nouns at runtime via the v4a §137 pack verb contract; pack-contributed words are reserved only while the pack is loaded, and the base 34 are permanent.

### Verbs (10)

| Verb | Purpose |
|---|---|
| `remember` | Store a value, list, record, or named composition (optionally with a `from <param>` parameter — v2d §96) |
| `show` | Display the value of a named item or one field of a record (`show total of order1`); `show "literal text"` displays the quoted content (v2c §88) |
| `filter` | Reduce a list in-place by a condition |
| `keep` | Non-destructive sibling of `filter` — returns matches as a fresh list; source unchanged. v2a §67. |
| `count` | Return (and auto-show) the size of a list |
| `gather` | Generate a numeric range, store and auto-show it |
| `combine` | Sum the numbers in a list (non-destructive, auto-shows) |
| `each` | Iterate over a list and perform an action per item; supports `show A and B` for multi-field display (v2a §69) |
| `choose` | Conditional branching via `choose if <cond>: <action> [otherwise [if <cond>:] <action>]*` (v2d §99) |
| `finish` | Exit listener mode immediately and totally — legal only inside a `when` action block (v3a §112) |

### Connectives (14)

| Connective | Purpose |
|---|---|
| `where` | Introduces a filter condition |
| `and` | List construction; compound condition; operation sequencing; record-field continuation; multi-field display in `each ... show` (five contexts, all deterministically disambiguated) |
| `or` | List construction; compound condition; operation sequencing; record-field continuation (four contexts) |
| `from` | Range start; result capture; simple reference; composition parameter declaration and passing (v2d §96) |
| `with` | Introduces values, list items, or record fields |
| `called` | Introduces a name |
| `to` | Range endpoint, or component of `equal to` |
| `how` | Signals a named-composition definition (with `to`) |
| `as` | Field assignment in records |
| `of` | Single-record field access — `<field> of <record>` in any value position (v2a §68 + v2b §77) |
| `if` | Introduces a `choose` branch's condition (v2d §99) |
| `otherwise` | Introduces a `choose` alternative or terminal branch (v2d §99) |
| `when` | Registers a reactive handler — top-level only; introduces an indented action block (v3a §108/§110) |
| `unless` | Guard clause on a `when` line — compound eligibility is `when-true AND NOT unless-true` (v3a §109) |

### Operators (5)

| Operator | Meaning |
|---|---|
| `is` | Comparison introducer OR equality operator (disambiguated by one-token lookahead) |
| `above` | Strictly greater than |
| `below` | Strictly less than |
| `equal to` | Multi-word operator for explicit equality |
| `not` | Modifier producing distinct semantics — `not above N` is ≤ N (includes the boundary), distinct from `below N` (§21 line 416) |

### Articles (3)

`the`, `a`, `an`. Decorative — the parser ignores them where they appear. (Including `an` is v1c §47; the inception checkpoint originally listed only `the` and `a`.) Descriptors between an article and `called` (`a domain called X`) are also decorative for semantics but are preserved verbatim in the canonical rendering — your wording reads back the way you wrote it (v2a §71).

### Delimiter (1)

`:` separates a composition name from its body, and a `choose` branch's condition from its action (v2d §99).

### Quoting (v2c)

`"..."` brackets a multi-word string value or one that would collide with a reserved word (e.g. `with status as "in progress"`, `with label as "filter"`). Quotes are legal in value positions only — names and field names use hyphens for multi-word identifiers (`big-orders`, `start-date`). The renderer's conditional-quoting rule preserves quotes around values that need them and drops them around safe single-word values, so round-trips stay readable. (v2c §86–§92)

### v2-deferred (2)

`transform` and `compare` — reserved-word slots protected (v1a §29 / v3a §124). The grammar for these verbs is not yet specified; they're reserved so user-provided names won't collide when a future addendum lands them.

---

## The pipeline

Inscript has five core processing stages — lexer, reorderer, parser, semantic analyzer, and interpreter — with canonical rendering and structured-result handling around them. Each stage returns data; only the CLI wrapper performs I/O (v1d §64). v3a adds a Phase 2 runtime layer atop this pipeline that activates when `when` blocks register handlers.

### Phase 1 — sequential (v2d-identical)

1. **Lexer.** Splits a line into typed tokens. Case-insensitive; strips decorative punctuation at word edges (interior `.` in `3.14` survives); combines `equal to` into a single operator token via one-word lookahead; recognizes blank lines as no-ops; accumulates `"..."` runs as `QUOTED_STRING` tokens (v2c §86); reports leading-tab indentation as a parse error (v3a §110). (inception §22; v1c §47–§48; v2c §86–§92)

2. **Reorderer.** Narrow table-driven preprocessor that accepts canonical word order, target-before-verb (`the orders filter where ...`), and bare target-before-verb. Other arrangements are rejected with a canonical-form suggestion. The full free-order acceptance is the target state for the tile interface, not the v1 text interpreter. (v1d §55)

3. **Parser.** Slot-filling per verb signature. Implements all v1b §44 disambiguation rules — `and`, `or`, `is`, `not`, `to`, `from`, `each` — deterministically via parser state and one-token lookahead. Produces a typed AST. Mixed `and`/`or` in any condition triggers amber-precedence (extended to `when`/`unless` at v3a §123). A second entry point, `parse_when_block(header, action_lines)`, handles v3a §110 indented action blocks: same-depth throughout, deeper-than-block is a parse error, empty blocks are a parse error. (inception §21; v1a §30; v1b §44; v1c §51; v3a §108–§110)

4. **Semantic analyzer.** Checks names against the symbol table, types against operations, field schemas across record lists (every record must have the referenced field, v1d §60), list homogeneity (v1d §59), gather range direction and cap (v1d §62/§63). For named compositions, grammar is validated at definition time and names at call time (§23 line 466). v3a extends the analyzer with two listener-aware kwargs (`in_action_block`, `live_value_names`) for the §111/§112/§117 ownership and `finish`-context rules.

5. **Interpreter.** Executes the validated AST against a mutable symbol table. In-place `filter`, non-destructive `combine`, `gather` stores-and-shows, copy semantics for all data operations, iterator context for `each`, stepwise commit for multi-operation sequences. Phase 1 `WhenNode` statements register into a handler table rather than executing — the action block is parsed but not run until Phase 2 (v3a §108). (§24; v1b §38–§42; v1c §49; v1d §56–§58)

A thin CLI wrapper is the only module that calls `input()` or `print()`. Every other module returns a structured `InscriptResult`. (v1d §64)

### Phase 2 — reactive listener (v3a)

Phase 2 starts only if Phase 1 completes with zero errors AND at least one `when` handler registered (§107 gate). The runtime then:

1. **Listener entry marker.** Yields a `LISTENING` result with the union of all handler dependency names (§122).

2. **Initial evaluation.** Every registered handler's compound eligibility is evaluated against the current symbol table; any handler that is already eligible fires in registration order with `trigger.source = "initial"` (§121). Cascades resolve depth-first.

3. **Adapter dispatch + event loop.** Each registered domain pack's adapter is attached to the shared, thread-safe event queue and started (§116/§119). The runtime drains one `(name, value)` update at a time to completion — change detection uses deep Inscript value equality (§113), edge-triggered firing on false→true transitions (§115).

4. **Cascading + cycle detection.** Action-block mutations are coalesced by name after the action block completes (§113); modified-name dependents re-evaluate and fire depth-first. The conservative cycle guard rejects same-handler-twice in one cascade chain with `ERROR_RUNTIME` (§114). The handler stays active for future events.

5. **Shutdown.** A `SHUTDOWN` result is yielded when `finish` executes (§112), when all adapters signal completion or fail (§120), or on external termination — with metadata.reason identifying which.

Domain packs are registered externally — either via the CLI `--pack <path>` flag (JSON config) or via the `Session(domain_packs=...)` constructor (§118). v3a ships exactly one adapter (`TestAdapter`) for scripted, deterministic event-driven testing.

---

## Nine outcomes

Every Phase 1 sequential statement produces exactly one of five outcomes (v1c §50):

| Outcome | When | Behavior |
|---|---|---|
| **Success** | Parse + analysis + execution all succeed | Canonical preview displayed; output (if any) written |
| **Amber — precedence** | Mixed `and`/`or` in any `where`/`choose`/`when`/`unless` condition | Parser's interpretation shown with parens; user confirms or restructures |
| **Amber — ambiguity** | Reorderer cannot uniquely resolve slot filling | Clarification prompt; no execution until clarified |
| **Error — parse** | Cannot build an AST (no verb; reserved word in name position; vocabulary word in value position; malformed clause; indentation rule violated) | Plain-English error describing what is missing |
| **Error — semantic** | AST built but references a non-existent name, wrong type, missing field, out-of-range gather, `finish` outside an action block, `remember`/`filter` on a live-value name, etc. | Plain-English error; nothing executed |

Phase 2 listener mode adds four more (v3a §122):

| Outcome | When | Behavior |
|---|---|---|
| **Listening** | Phase 2 begins | One-time entry marker carrying the set of watched names |
| **Handler fire** | An action-block statement runs successfully during firing | Same display shape as Success; wrapped with `trigger` metadata (source, handler index, names changed, new values) |
| **Shutdown** | `finish`, all adapters complete, no adapters registered, or external termination | Terminal result with `reason` metadata |
| **Error — runtime** | Cycle detected (same handler firing twice in one cascade chain), adapter failure, or adapter type mismatch | Plain-English error with `kind` metadata; the handler remains active for future events |

No "warning" category. No silent fallback. The interpreter is deterministic — the prose either runs as written or it doesn't run at all. (v1c §52)

---

## Example programs

### Program 1 — basic values and lists

```
remember a number called age with 30
remember a list called colors with red and blue and green
show age
show colors
count the colors
```

```
30
red, blue, green
3
```

`count` auto-shows because it is a standalone expression that produces a value (§24). The descriptor `number` between `a` and `called` is decorative — type is inferred from the value (v1b §36).

### Program 2 — structured records and iteration

```
remember an order called order1 with total as 75 and status as active
remember an order called order2 with total as 30 and status as active
remember an order called order3 with total as 120 and status as pending
remember a list called orders with order1 and order2 and order3
each the orders show total
```

```
75
30
120
```

`each` binds an iterator context (v1c §49) so `show total` resolves `total` as a field on the current record. Records are copied into the list (§24 line 486) — mutating `order1` later does not affect `orders[0]`.

### Program 3 — filtering and chaining

```
filter the orders where total is above 50
show orders
filter the orders where status is active
count the orders
each the orders show status
```

```
total: 75, status: active
total: 120, status: pending
1
active
```

`filter` modifies `orders` in place (§24). After both filters, only `order1` remains. `show` on a list of records emits one record per line, formatted as `field: value, field: value` (v1b §42).

### Program 4 — numbers, range, and capture

```
gather the numbers from 1 to 10
filter the numbers where each is above 5
count the numbers
combine the numbers
remember the result called total from combine the numbers
```

```
1, 2, 3, 4, 5, 6, 7, 8, 9, 10
5
40
```

Inside a `where` clause `each` is a pronoun for the current item, not the iteration verb (v1b §37). `combine` is non-destructive (v1b §39), so the final `remember ... from combine the numbers` captures 40 while `numbers` still contains `[6, 7, 8, 9, 10]`. The `from <verb-phrase>` construct triggers recursive descent in the parser (v1b §43).

### Program 5 — the `not` operator

```
gather the scores from 1 to 10
filter the scores where each is not above 7
filter the scores where each is not below 3
filter the scores where each is not equal to 5
```

After all filters, `scores` is `[3, 4, 6, 7]`. `not above 7` means `≤ 7` (the boundary is included), which is distinct from `below 7` which excludes it — `not` is a genuine operator modifier with its own comparison semantics, not a synonym swap (§21 line 416).

### Multi-word strings (v2c)

```
remember an order called o1 with total as 75 and status as "in progress"
remember a value called priority-label with "high priority"
show priority-label
show "Section A: counts before filtering"
```

```
high priority
Section A: counts before filtering
```

The quoting mechanism is the v2c resolution to D7: values that contain spaces or that collide with reserved words (`"filter"`, `"if"`) wrap in `"..."` and bypass the vocabulary table. Names and field names still use hyphens (`priority-label`, `start-date`) — quotes are value-position only. The renderer drops quotes around single-word non-reserved values to keep round-trips clean (§90). (v2c §86–§92)

### Composition parameters + `choose` (v2d)

```
remember a list called big-orders with order1
remember a list called small-orders with order2
remember how to find-high from data: keep the data where total is above 50

remember the high-from-big called bigwins from find-high from big-orders
remember the high-from-small called smallwins from find-high from small-orders

remember a number called score with 75
choose if score is above 90: show "excellent" otherwise if score is above 50: show "passing" otherwise show "needs work"
```

`find-high` takes one parameter declared with `from <param>` in the definition and passed with `from <name>` at the call site (v2d §96). The composition is reusable on different lists — its body sees `data` bound to the passed list for the duration of the call. `choose` selects the first branch whose condition is true, or the terminal `otherwise` if none match. `if`/`otherwise` are new connectives (v2d §99); the colon is the context switch between condition and action.

### Event-driven listener (v3a)

```
remember a number called level with 0
remember a string called alert-mode with off

when level is above 100
  remember a string called alert-mode with on
  show "level escalated"

when alert-mode is equal to on
  show "alarm sounding"

when level is above 200
  choose if level is above 250: finish otherwise show "warning very high"
```

A `when` line at indent 0 starts an indented action block (min 1 space, tabs rejected, same depth throughout — v3a §110). Each `when` registers a reactive handler; the action block is parsed but not executed during Phase 1. Phase 2 starts after Phase 1 completes with zero errors: handlers fire when their compound eligibility transitions false→true. Updates arrive from an externally-registered domain pack (e.g. `--pack pack.json` for the test adapter — v3a §118). `finish` exits listener mode immediately and totally — no further statements, cascades, or queued updates run after it executes.

Cascades work because action-block writes are watched too: setting `alert-mode` to `on` inside the first handler's action triggers the second handler's eligibility transition. The conservative cycle guard (§114) catches genuinely-toggling handler pairs as a runtime error rather than letting them loop.

### Named compositions

```
remember how to find-big-orders: filter the orders where total is above 50
remember how to count-active: filter the orders where status is active and count the orders
```

Stores verb phrases under user-defined names. Calling a composition runs its stored AST against the current symbol table. Names inside the body are resolved at call time, not at definition time (§23 line 466) — so a composition can reference data that does not yet exist when the composition is defined.

v1 calls a composition by its name alone (e.g. `find-big-orders`). Composition parameters and `from`-chaining are deferred to v2 (v1b §41).

### Mixed precedence — amber example

```
filter the orders where total is above 50 and status is active or status is pending
```

The parser deterministically reads this as `(total is above 50 AND status is active) OR status is pending` (standard precedence). Mixed `and`/`or` in a single `where` clause triggers an amber prompt before execution:

> I'll read this as: (total is above 50 and status is active) or status is pending. Is that what you mean? If not, split it into two statements.

The user confirms or rewrites. The parse is unambiguous; the amber exists because non-programmer intuition about boolean precedence is unreliable. (v1a §30)

### Stepwise execution

```
remember a list called nums with 1 and 2 and 3 and 4 and 5
filter nums where each is above 3 and show missingname
show nums
```

Line 2 is a two-operation sequence. The filter succeeds and `nums` becomes `[4, 5]` in place. Then `show missingname` fails. The error message names the prior success:

> I completed 'filter the nums where each is above 3' but then I can't find 'missingname'. You might need to 'remember' it first. The filter has already been applied.

Line 3 then shows `4, 5` — the filter's commit persists. Multi-operation sequences are stepwise, not transactional. There is no rollback. (v1d §56)

---

## Current scope and deferrals

The shipped build covers v1 (48 locked test sentences) + v2a (11 more) + UX polish + v2.1-patches + v2b (9 more) + v2c (12 more) + v2d (15 more) + v3a (18 more) + v3b (4 more) + v4a (10 more). **713 tests passing.** Larger scope is intentionally deferred — but the sequential feature set (v1 → v2d), the reactive feature set (v3a/v3b), and the pack-verb extension contract (v4a) together form a structurally complete programming language.

**Currently shipped.** Two-phase execution (Phase 1 sequential, Phase 2 reactive). 10 base verbs. 14 connectives. 34 base reserved words. Numbers (integers + decimals). Strings (single-token bare words + multi-word quoted strings via v2c, with verbatim case preservation per v3b §127). Lists (homogeneous — all numbers, all strings, or all records). Records (named fields, with descriptor preserved on the symbol for pack-verb type checks). Named compositions with optional parameters (v2d §96). Conditional branching via `choose if/otherwise` (v2d §99). In-place `filter`, non-destructive `keep`, non-destructive `combine`, copy semantics, iterator context for `each`, multi-field display in `each ... show`, single-record field access via `show <field> of <record>` and `<field> of <record>` in any value position. Descriptor preservation, named-offender error wording, stepwise sequences. Composition return values via `remember the X from <comp>` (v2b §76). Event-driven `when`/`unless`/`finish` with indented action blocks (v3a §110), single-threaded event queue (v3a §119), edge-triggered evaluation with deep value equality (v3a §113), depth-first cascading with conservative cycle detection (v3a §114), domain-pack adapter contract (v3a §116) registered externally via `--pack <path>` JSON or `Session(domain_packs=...)`. v4a general-purpose pack verb contract (§137) — packs declare verbs with slot signatures + type constraints + execution dispatch in JSON; the parser dispatches pack verbs after base verbs, the analyzer enforces descriptor-based type constraints, and `set_value` is the first execution type. The UI domain pack (§134) ships 10 component nouns and the `navigate to <screen-name>` verb. CLI flags `--quiet`, `--test`, `--pack` (any position).

**Not built (deliberately).** Tile-composition interface. Proposal engine and authorize-don't-author authoring flow. Real-world domain packs (healthcare, smart home, game) — the language ships a test adapter only, packs are product work. Domain pack activation syntax (an Inscript-level `use`/`load` verb). The verbs `transform`, `compare` — reserved-word slots protected, no grammar yet. Symbolic syntax surface. External data sources beyond domain-pack adapters. Negative numbers. Scope isolation beyond the iterator context and composition parameters. Mixed-type lists. Descending ranges. Ranges over 10,000 items. Nested records (and therefore chained `of`). `choose` inside `each`. Sophisticated cycle detection beyond same-handler-twice. Adapter timeout or preemption. Tile interface, proposal engine, domain packs as product surfaces.

The deferrals are not "TODO when we get to it." Each has a specific reason and a documented v2/v3 plan — see [`docs/roadmap/v1-v2-boundary.md`](docs/roadmap/v1-v2-boundary.md) for a readable walkthrough, or `docs/spec/inscript_addendum_v1d_build_boundary.md` §66 (and v2a §75, v2b §84, v2d §103, v3a §126) for the locked source.

---

## Design principles

These are the load-bearing decisions that shape every implementation choice. Each is locked in a specification document and was reaffirmed before any Python was written.

**The prose IS the program.** The interpreter operates exclusively on what the user stated. It does not infer, assume, guess, or fill in unstated information. If the prose doesn't say it, it doesn't happen. (v1c §52)

**The vocabulary is the boundary.** 34 reserved words in the current build. v2c added a quoting mechanism for multi-word string values, but only in value positions — names and field names still come from the unquoted name-space. Vocabulary words cannot appear unquoted as user-provided names or as string values. This is structurally why slot-filling parser logic works: every word's category is known in advance. Each addition to the vocabulary (v2a's `keep`, v2a's `of`, v2d's `choose`/`if`/`otherwise`, v3a's `when`/`unless`/`finish`) is the smallest spec change consistent with a dogfooded gap. (v1a §29; v1c §46; v2a §73; v2d §104; v3a §124)

**The reorderer does not guess.** When an arrangement of words could fill slots in more than one valid way, the system produces an amber clarification prompt rather than picking one interpretation. Authorship over inference. (inception §17)

**Authorize, don't author.** The on-ramp is modification of a working program, not authorship from a blank file. Programming starts from something that runs. (v7.5g §19; v1a §32)

**Canonical prose rendering as intent verification.** The parser produces a canonical English sentence reconstructed from the AST. The user sees what the parser understood before execution runs — including, critically, on obfuscated or scrambled input. The AST cannot lie. (v1a §33)

**Stepwise execution, not transactional.** Multi-operation sequences commit independently. If a later operation fails, earlier side effects remain and the error message names what was completed. The simplest model consistent with sequential interpretation, and matches non-programmer intuition. (v1d §56)

**Designed from liberation pedagogy by a non-programmer.** The design origin produces different design decisions at every layer. The vocabulary, the error messages, the verb semantics, the amber-not-error pattern — each one would have been different if a programmer had chosen.

---

## Project structure

```
inscript/
├── CLAUDE.md                        Build instructions for Claude Code
├── BUILD_PLAN.md                    Seven-phase v1 build plan (historical)
├── README.md                        (this file)
├── pyproject.toml                   Python project config
├── docs/spec/                       Specification documents (immutable)
│   ├── inscript_inception_checkpoint_v1.md
│   ├── inscript_addendum_v1a_pre_build.md
│   ├── inscript_addendum_v1b_design_resolutions.md
│   ├── inscript_addendum_v1c_implementation_hardening.md
│   ├── inscript_addendum_v1d_build_boundary.md
│   ├── inscript_addendum_v2a_dogfooding_resolutions.md
│   ├── inscript_addendum_v2b_composition_returns.md
│   ├── inscript_addendum_v2c_multi_word_strings.md
│   ├── inscript_addendum_v2d_parameters_and_branching.md
│   ├── inscript_addendum_v3a_event_driven_execution.md
│   ├── inscript_addendum_v3b_quoted_string_case_preservation.md
│   ├── inscript_addendum_v4a_pack_verbs_and_port.md
│   └── inscript_v1_thirty_sentences.md
├── src/inscript/
│   ├── vocabulary.py                Token types, reserved-word sets, verb signatures
│   ├── lexer.py                     Tokenization + `leading_indent` (v3a §110)
│   ├── reorderer.py                 Narrow table-driven reorderer
│   ├── parser.py                    Slot-filling parser; AST nodes; `parse_when_block`
│   ├── renderer.py                  AST-to-prose canonical rendering (multi-line for WhenNode)
│   ├── analyzer.py                  Semantic analysis; SymbolEntry; iterator context; v3a `in_action_block` / `live_value_names`
│   ├── interpreter.py               Phase 1 execution; HandlerTable; ContextVars; `_FinishRequested`
│   ├── listener.py                  Phase 2 generator — initial eval, event-queue drain, cascades, cycle detection, shutdown (v3a §107–§122)
│   ├── adapter.py                   DomainPack, Adapter, TestAdapter, LiveValueRegistry (v3a §116–§120)
│   ├── result.py                    InscriptResult + ResultStatus (9 statuses)
│   ├── cli.py                       Session + REPL + file driver + `--pack` (only module with input/print)
│   └── __main__.py                  `python -m inscript` entry point
├── tests/
│   ├── test_vocabulary.py           Vocab tables + reserved-word categorization
│   ├── test_result.py               Result interface (9 statuses + metadata)
│   ├── test_lexer.py                Tokenizer + `leading_indent`
│   ├── test_reorderer.py            Reorderer table
│   ├── test_parser.py               Parser + `parse_when_block`
│   ├── test_renderer.py             Canonical rendering + round-trip
│   ├── test_analyzer.py             Semantic checks + v3a context kwargs
│   ├── test_interpreter.py          Phase 1 execution + HandlerTable + dependency extraction
│   ├── test_adapter.py              DomainPack / Adapter / TestAdapter / LiveValueRegistry
│   ├── test_listener.py             Phase 2 listener (initial eval, cascades, cycle, shutdown)
│   ├── test_integration.py          End-to-end coverage for v1 / v2a / v2b / v2c / v2d sentences
│   ├── test_integration_v3a.py      End-to-end for v3a sentences 96–113
│   ├── test_integration_v4a.py      End-to-end for v4a sentences 118–127 (UI pack + navigate)
│   └── conftest.py                  Autouse fixture: resets pack vocabulary between tests (v4a §137)
└── examples/
    ├── program1_basics.insc
    ├── program2_orders.insc
    ├── dogfood_*.insc               Per-addendum dogfood programs + .actual.txt baselines
    ├── dogfood_v3a_event_driven.insc
    ├── dogfood_v3a_pack.json        Test domain pack for the v3a dogfood
    ├── dogfood_navigate_test.insc   v4a smoke test for `navigate to <screen>`
    └── pack_ui.json                 v4a UI domain pack: 10 nouns + `navigate` verb
```

713 tests pass via `pytest tests/`. Each spec section that locks a behavior has at least one test that exercises it.

---

## The locked test sentences

The test suite is built around locked test sentences that are simultaneously:

- A test case for the lexer, parser, analyzer, and interpreter.
- A grammar artifact — the sentences ARE the discovered grammar; design questions that emerged while writing them become the resolutions in v1b §36–§43, v1c §46–§52, v1d §55–§66, v2a §67–§72, and v2b §76–§81.
- A specification — when the documents and the sentences disagree, the conversation is structured around resolving the inconsistency before any code is written.

Sentence numbering accumulates across addenda:

| Source | Sentences | Coverage |
|---|---|---|
| `inscript_v1_thirty_sentences.md` | 1–30 | The original thirty: every verb in simple + complex forms |
| v1c §53 | 32–34 | Reserved-word value position, article `an`, no-verb error |
| v1d §65 | 35–48 | Hostile test block — error paths across all categories |
| v2a §74 | 49–59 | `keep` basic + capture + composition reuse, `of` field access, multi-field `each show`, composition-chaining error |
| v2b §83 | 60–68 | Composition returns, generalized `of` in where/with positions, list-model clarification |
| v2c §94 | 69–80 | Quoting mechanism: multi-word values, quoted reserved words, conditional rendering, name/field rejection |
| v2d §105 | 81–95 | Composition parameters with `from`, parameterized calls in value-capture position, `choose if`/`otherwise`, multi-statement branches |
| v3a §125 | 96–113 | `when` + `unless` + `finish`, initial evaluation, cascades, cycle detection, unset live values, no-adapter shutdown, Phase 1 error blocks Phase 2 |
| v3b §131 | 114–117 | Quoted-string case preservation across lex, render, and `where` equality |
| v4a §140 | 118–127 | `navigate to <screen>` basic + semantic errors + parse error, UI components with known and freeform fields, `when` on UI components, `navigate` inside an action block, pack-verb reserved-word check, pack noun usable as name without pack |

All 127 sentences are wired through the test suite. v1/v2a/v2b/v2c/v2d coverage lives in `tests/test_integration.py`; v3a in `tests/test_integration_v3a.py`; v4a in `tests/test_integration_v4a.py`. The full suite is 713 tests.

---

## Guides

Human-readable guides live under `docs/`. They are derived from the
locked specifications but written for fluent reading rather than
authority. The specifications remain the source of truth when wording
matters.

| Guide | What it covers |
|---|---|
| [`docs/language/quickstart.md`](docs/language/quickstart.md) | Install, run tests, run an example, start the REPL, and try a three-line demo program. |
| [`docs/language/syntax.md`](docs/language/syntax.md) | Full syntax tour: source-file rules, all ten verbs, lists, records, conditions, `each`, named compositions with parameters, `choose`, quoting, and the v3a `when`/`unless`/`finish` listener model. |
| [`docs/architecture/pipeline.md`](docs/architecture/pipeline.md) | Stage-by-stage walkthrough of how a source line becomes a result, the Phase 2 listener layer for v3a, the nine-outcome trust model, and the I/O boundary. |
| [`docs/roadmap/v1-v2-boundary.md`](docs/roadmap/v1-v2-boundary.md) | What v1 includes and what it intentionally does not, with each deferral framed as a design boundary. |

---

## Specification documents

The build specification has grown by addendum. Each document either locks new decisions or closes gaps surfaced by external review or by dogfooding the previous ones. Earlier documents are never overwritten — additions extend the section numbering.

| Document | Status | Locks |
|---|---|---|
| `inscript_inception_checkpoint_v1.md` | Locked + implemented | Vocabulary (§11), pipeline (§8–§9), verb signatures (§17), parser rules (§21–§22), interpreter behaviors (§24), v1/v2 scope (§25) |
| `inscript_addendum_v1a_pre_build.md` | Locked + implemented | Reserved-word exclusion (§29), mixed-precedence amber (§30), AST-state-filtered tile tray (§31), authorization-requires-compositional-act (§32), canonical prose rendering (§33) |
| `inscript_addendum_v1b_design_resolutions.md` | Locked + implemented | Eight design resolutions surfaced by the thirty test sentences (§36–§43); complete parser disambiguation ruleset (§44) |
| `inscript_addendum_v1c_implementation_hardening.md` | Locked + implemented | Vocabulary words can't be values (§46), article `an` (§47), blank-line handling (§48), iterator context (§49), output taxonomy (§50), parser lookahead capability (§51), deterministic interpretation (§52) |
| `inscript_addendum_v1d_build_boundary.md` | Locked + implemented | Reorderer scope (§55), stepwise execution (§56), case normalization (§57), duplicate overwrite (§58), homogeneous lists (§59), record schema homogeneity (§60), single-token strings (§61), descending ranges (§62), gather range cap (§63), structured results (§64), build boundary (§66) |
| `inscript_addendum_v2a_dogfooding_resolutions.md` | Locked + implemented | `keep` verb (§67), `of` connective (§68), multi-field `each show` (§69), composition-chaining error message (§70), descriptor preservation (§71), D7 deferral (§72), updated vocabulary table (§73), test sentences 49–59 (§74) |
| `inscript_addendum_v2b_composition_returns.md` | Locked + implemented | Composition return values (§76), generalize `of` to all value positions (§77), list/iteration model clarification (§78), U7/U8/U9 (§79–§81), test sentences 60–68 (§83) |
| `inscript_addendum_v2c_multi_word_strings.md` | Locked + implemented | Quoting mechanism: lexer quote-state (§86), `QUOTED_STRING` in value positions only (§87), literal display via `show "..."` (§88), quoted reserved words bypass vocabulary exclusion (§89), conditional rendering (§90), case normalization inside quotes (§91), empty quotes rejected (§92), test sentences 69–80 (§94) |
| `inscript_addendum_v2d_parameters_and_branching.md` | Locked + implemented | Composition parameters with `from` (§96), parameter-mismatch errors (§97), parameterized calls in value-capture position (§98), `choose if`/`otherwise` (§99–§102), `transform`/`compare` deferral (§103), vocabulary update (§104), test sentences 81–95 (§105) |
| `inscript_addendum_v3a_event_driven_execution.md` | Locked + implemented | Two-phase execution (§107), `when` registration (§108), `unless` guard (§109), indented action blocks (§110), action block scope and live-value rules (§111), `finish` verb (§112), edge-triggered evaluation (§113), cascading + cycle detection (§114), registration-order firing (§115), adapter contract (§116), live-value lifecycle (§117), domain pack registration (§118), single-threaded event queue (§119), adapter failure isolation (§120), initial evaluation (§121), result interface (§122), amber at registration (§123), vocabulary update (§124), test sentences 96–113 (§125) |
| `inscript_addendum_v3b_quoted_string_case_preservation.md` | Locked + implemented | Quoted-content case preservation (§127 — supersedes v2c §91), case-bearing as third conditional-quoting trigger (§128), migration impact (§129), vocabulary unchanged (§130), test sentences 114–117 (§131) |
| `inscript_addendum_v4a_pack_verbs_and_port.md` | Locked + implemented (Python; TypeScript port lives in the Möbius monorepo) | UI domain pack vocabulary (§134), `navigate` as pack-level verb (§135), component schemas with freeform overflow (§136), general-purpose pack verb contract (§137), TypeScript port scope (§138), build phases (§139), test sentences 118–127 (§140) |
| `inscript_v1_thirty_sentences.md` | Test specification | 1–30 + v1c §53 (31–34) + v1d §65 (35–48) + v2a §74 (49–59) + v2b §83 (60–68) + v2c §94 (69–80) + v2d §105 (81–95) + v3a §125 (96–113) + v3b §131 (114–117) + v4a §140 (118–127) = 127 sentences |

Two triage documents and two gap inventories under `docs/` show how each addendum was scoped against dogfooding evidence:

| Document | Role |
|---|---|
| `docs/inscript_gap_inventory_2026_05_12_v1_dogfooding.md` | v1 dogfooding gaps (D1–D8 + UX items) — input to v2a |
| `docs/inscript_v2_design_triage_2026_05_12.md` | Triage of D1–D8 — feeds v2a |
| `docs/inscript_gap_inventory_2026_05_12_v2a_dogfooding.md` | v2a dogfooding gaps (D9–D11 + UX items) — input to v2b |
| `docs/inscript_v2b_design_triage_2026_05_12.md` | Triage of D9–D11 + UX items — feeds v2b |

The spec documents are immutable build artifacts. The code is built against them, not the other way around. When the builder encountered an ambiguity, the choice was to read the relevant document — not to pattern-match or guess.

---

## Lineage

Inscript is the fifth expression of one thesis at different layers:

1. **Narratia.** Educational storytelling. Built on Paulo Freire's pedagogy of the oppressed — learners author their own narratives rather than absorb dominant ones.
2. **Counter-Flow.** A reading-pace experiment. The reader's tempo, not the text's.
3. **TAOS.** Accountability infrastructure. The governed must remain author of the system's accountability.
4. **Möbius Inscript.** A behavioral-rules DSL with prose-as-syntax, tile composition, and authorize-don't-author. The thesis applied to rule authoring within Möbius.
5. **Inscript Programming Language.** The thesis applied to general computation. The same principles, scaled. *(This repository.)*

Each is the same idea — *the person affected must remain the author of their story* — applied to a different layer.

The Möbius Inscript system is a DSL for behavioral rules within Möbius. The Inscript Programming Language is its principles applied to general-purpose computation. They share a lineage and a name; they are not the same system.

---

## Architects and builders

| Role | Person |
|---|---|
| Architect, language designer | Rob Thomas (R. Michael Thomas) |
| Interpreter builder | Claude Code |
| Build sessions | May 11–13, 2026 (v1 → v2a → UX polish → v2.1-patches → v2b → v2c → v2d → v3a → v3b → v4a Phase 1 Python → v4a Phase 2 TypeScript port in Möbius) |

The build is a paired collaboration. The architect produces and approves every design decision in the locked specification documents. The builder translates those decisions into Python — and, when implementation surfaces an ambiguity, opens the spec document rather than guessing. The CLAUDE.md rule: every claim is load-bearing; do not state that a spec section says something without verifying. The rhythm — *spec → dogfood → triage → spec → implement* — is what keeps the language shape coherent across additions.

---

## Status and what's next

**Currently shipped.** v1 → v2d (sequential) + v3a/v3b (event-driven listener mode + quoted-string case preservation) + v4a (pack verb contract + UI domain pack). 713 tests passing. The interpreter runs in a terminal as text-only, reads `.insc` source files, and offers an interactive REPL with `--quiet`, `--test`, and `--pack` flags. A separate TypeScript port (lexer/reorderer/parser/analyzer/renderer — no interpreter) lives in the Möbius monorepo at `packages/inscript-lang/` and validates the same 127 sentences against this implementation as its sync contract (v4a §138).

**The largest remaining work is not language additions.** It's everything around the language — Branches C/D/E from the inception checkpoint, plus domain packs as product surfaces. Specifically:

- **Branch C — Tile interface.** Apply the slot-filling architecture to a visual tile-composition surface with AST-state-filtered tray (v1a §31). The interpreter is the engine; the tile surface is one of three views of the same AST.
- **Branch D — Identity and positioning.** Name decision (Inscript Programming Language vs. a distinct name from Möbius Inscript). Repository setup. License choice. README as manifesto.
- **Branch E — Narratia integration.** The proposal engine that powers "authorize, don't author." Observes intent, proposes a working program for the user to modify.
- **Domain packs as product surfaces.** Healthcare, business, home automation, narrative, legal/compliance. Each pack adds 10–15 context-specific terms (inception §19) plus an adapter implementation. v3a ships only the `TestAdapter` for scripted, deterministic event-driven testing — real-world packs are downstream product work, not language work.

**Smaller language additions still on the deferred list** (in no particular order):

- **`transform` and `compare` verbs.** Reserved-word slots protected through v3a §124; no grammar yet specified. These would extend the verb set if a dogfooded gap surfaces a clear use case.
- **`choose` inside `each`.** Deferred at v2d §102; deliberately closed in v3a §126. The list-level filtering model handles the discriminative cases that motivated it.
- **Sophisticated cycle detection.** v3a §114's same-handler-twice guard is conservative — a more nuanced state-based detector could allow legitimately-terminating patterns that the current guard rejects. Deferred until a real use case demands it.
- **Adapter timeout and preemption.** v3a §119's single-threaded queue assumes handlers complete quickly. A long-running handler blocks the queue; acceptable for v3a, revisitable later.
- **Domain pack activation via language syntax.** v3a §118 registers packs externally (constructor / CLI). An Inscript-level `use`/`load` verb would let programs declare their adapter dependencies inline.

---

## License

License decision is deferred — see inception §26 open question Q10. Liberation infrastructure should be open from day one; the specific license is a Branch D concern.

---

*Freire said the oppressed must name their own world.*
*A programming language is a tool for naming.*
*The question was never whether non-programmers could think computationally.*
*The question was why we kept handing them someone else's language to do it in.*

*Begin anywhere.*

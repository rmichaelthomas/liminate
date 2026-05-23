# Liminate Programming Language

A prose-as-syntax programming language designed from the human end.

> *"Every programming language in history was designed by programmers. This one wasn't. That's why the design is different."*

**Status (May 22, 2026):** v1 interpreter + v2a (`keep`, `of`, multi-field `each show`, descriptor preservation) + UX polish (`--quiet`, named-offender errors, auto-show truncation) + v2.1-patches + v2b (composition return values, generalized `of`) + v2c (quoting mechanism for multi-word strings) + v2d (composition parameters with `from`, `choose` verb with `if`/`otherwise`) + v3a event-driven execution (`when`/`unless`/`finish`, two-phase listener model, single-threaded event queue, cascading triggers with cycle detection, domain-pack adapter contract) + v3b (quoted-string case preservation) + v4a pack verb contract (general-purpose JSON-defined pack verbs with slot signatures, type constraints, and execution dispatch; UI domain pack with 10 nouns + `navigate to <screen-name>`) + `add` verb addendum + `includes` connective / `remove` verb addendum + `within` connective with the session pack's `measure` verb + **Metabolic Era batch 1** (`weakens`/`over` — autonomous linear decay over a stated period of ticks) + **Normative Era batch 2** (`require`/`then` — enforcement and declared sequencing) + **Delegated/Epistemic Era batch 3** (`assign`/`expect` — item-to-recipient delegation and non-halting tracked anticipation) + **Infrastructure Era** (`by`/`plus`/`minus`/`multiplied by`/`divided by` — arithmetic expressions with PEMDAS precedence) + **Infrastructure Era batch 2** (`sort`/`reverse` — in-place list reordering by a field) + **V2 promotions** (`compare` — structured comparison into a `comparison` record; `transform` — per-element list mutation, the final V2-deferred word, so `V2_RESERVED` is now empty) + **Meta-Structural Era** (`about` — program topic declaration; `because` — statement-terminal quoted rationale on any verb statement; `inherited` — statement-initial provenance modifier with optional `from <agent>` attribution; all three are inert self-describing metadata, visible to rendering and `inspect` but never executed) + **Deontic Era** (`forbid` — halts with `PROHIBITION_VIOLATED` on a true condition, the mirror of `require`; `permit` — emits an informational line on a true condition and never halts, the `expect` pattern; together they complete the require/forbid/permit triangle) + **Temporal-Boundary Era** (`starting`/`until` — statement-initial connectives attaching quoted ISO 8601 effective dates and sunset clauses as inert metadata; temporal evaluation is a product-layer concern, not interpreter runtime). **1303 tests passing.** The sequential feature set (v1 → v2d), the reactive feature set (v3a/v3b), the pack-verb extension contract, the Metabolic Era's autonomous-time primitives, the Normative Era's enforcement-and-sequencing primitives, the Delegated/Epistemic Era's delegation-and-anticipation primitives, the Infrastructure Era's arithmetic-and-reordering primitives, the Meta-Structural Era's self-describing metadata, the Deontic Era's prohibition-and-permission verbs, and the Temporal-Boundary Era's effective-date-and-sunset connectives together form a structurally complete programming language; pack verbs let domains add vocabulary without touching the base 58 reserved words.

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
- [Lineage](#lineage)
- [Architects and builders](#architects-and-builders)
- [Status and what's next](#status-and-whats-next)

---

## What it is

`filter the orders where total is above 50` is not a prompt to an AI. It is the program.

Liminate is a general-purpose programming language whose source code is readable English prose. A bounded vocabulary of 54 words combines into sentences that execute directly. There is no separate code the prose generates — the sentence IS the program.

This is not a domain-specific language for queries or data, nor a natural-language layer over Python, nor a code-generating AI. It is a programming language with its own pipeline: lexer, reorderer, parser, semantic analyzer, interpreter. The prose-as-syntax constraint is structural, not cosmetic.

A `.limn` source file is plain text. One statement per line. Blank lines are skipped. Decorative punctuation (commas, periods, question marks, exclamation marks) is silently stripped — you can punctuate naturally.

---

## Why it exists

Programming languages are gatekeepers. They stand between human intent and computational execution, and they demand the human learn to speak the machine's language. Liminate inverts that: the machine learns to read English.

The use cases are not toys. Business rules, legal compliance, data filtering — domains where the person who understands the problem cannot currently express the solution in code. Healthcare protocols, smart home automation, narrative scripting — domains where the writer's document could BE the program. The translation step from intent to code is where errors, cost, and delay concentrate. Liminate eliminates the translation step.

The design comes from a non-programmer. Liminate's principles were designed before the architect understood compiler pipelines. The thesis: the person affected must remain the author. A language they can't read makes them not the author.

---

## What makes it different

Five properties combine in Liminate that exist individually in other systems but never together:

1. **Prose-as-syntax where the prose IS the executable code.** Not prose that generates code (vibe coding). Not prose that describes a game world (Inform 7, which is domain-locked). General-purpose computation expressed as readable English sentences that execute directly.

2. **Bounded vocabulary as design constraint.** 58 reserved words in the current build (21 verbs + 22 connectives + 8 single-word operators + `equal`/`multiplied`/`divided` as multi-word components + 3 articles + 1 declaration + 0 v2-deferred words — `V2_RESERVED` is now empty). The vocabulary is the language boundary, not a starter set that grows. Expressiveness scales through domain packs, composition over expansion, and named-composition chunking — not through adding more keywords. 

3. **Graduation from tiles to text within one language.** The same AST underlies a tile-composition surface (for first-encounter authoring), a prose surface (for fluent authoring), and an optional symbolic surface (for velocity). Three views, one structure. Scratch-to-Python is two languages; Liminate is one language with three surfaces. The v1 interpreter implements the prose surface; the tile surface is a separate downstream concern.

4. **Authorize, don't author.** The on-ramp is not a blank file. The system proposes a working program based on observed intent; the human modifies. First touch is on a working artifact. This requires at least one deliberate compositional act before commit — passive acceptance is not authorship.

5. **Designed from liberation pedagogy.** Liminate's design principles originate in Narratia, a storytelling platform built on Paulo Freire's pedagogy of the oppressed. The principle: people must remain authors of their own narrative — including the rules that govern their systems. Every design decision is checked against that principle.

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

A pure-Python equivalent would require introducing identifiers, defining a dict structure, writing a list comprehension, and using `print` calls in a for-loop. The Liminate program reads as the rule it expresses.

---

## Installation and running

Requires Python 3.10+.

```bash
git clone <repository-url>
cd liminate
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
python -m liminate examples/program1_basics.limn
```

Start an interactive REPL (`exit` or `quit` to leave):

```bash
python -m liminate
```

Test mode (auto-confirms amber prompts so a script doesn't pause):

```bash
python -m liminate --test examples/program2_orders.limn
```

Quiet mode (suppresses the canonical-prose echo; useful for any program longer than a few lines):

```bash
python -m liminate --quiet examples/dogfood_1_corpus_summary.limn
```

Phase 2 listener mode requires at least one registered domain pack (or a program that has no adapters, in which case the listener performs initial evaluation and shuts down). The `--pack <path>` flag loads a JSON test domain pack:

```bash
python -m liminate --pack examples/dogfood_v3a_pack.json --test --quiet \
    examples/dogfood_v3a_event_driven.limn
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

Multiple `--pack` flags accumulate. — domain pack activation via Liminate syntax (a `use`/`load` verb) is intentionally deferred; pack registration is external.

extends the pack JSON with optional `vocabulary` (noun additions to the reserved list while the pack is loaded) and `verbs` (slot signatures + execution dispatch). The shipped UI pack at `examples/pack_ui.json` adds 10 component nouns and the `navigate to <screen-name>` verb:

```bash
python -m liminate --pack examples/pack_ui.json --quiet \
    examples/dogfood_navigate_test.limn
```

Flags work in any argument position and can be combined. Blank source lines are mirrored to the output under `--quiet` so paragraph breaks survive.

Every statement is echoed first in canonical prose form (the parser's interpretation of what you wrote) before any output is shown — unless `--quiet` is set. This is the "Logic Preview" — see.

---

## The vocabulary

The current base vocabulary is 58 reserved words across six categories. The complete list is the entire language surface — no other words are part of Liminate, only user-provided names and literal values. Domain packs may add their own verbs and nouns at runtime via the pack verb contract; pack-contributed words are reserved only while the pack is loaded, and the base 58 are permanent.

### Verbs (16)

| Verb | Purpose |
|---|---|
| `remember` | Store a value, list, record, or named composition (optionally with a `from <param>` parameter) |
| `show` | Display the value of a named item or one field of a record (`show total of order1`); `show "literal text"` displays the quoted content |
| `filter` | Reduce a list in-place by a condition |
| `keep` | Non-destructive sibling of `filter` — returns matches as a fresh list; source unchanged.. |
| `count` | Return (and auto-show) the size of a list |
| `gather` | Generate a numeric range, store and auto-show it |
| `combine` | Sum the numbers in a list (non-destructive, auto-shows) |
| `each` | Iterate over a list and perform an action per item; supports `show A and B` for multi-field display |
| `choose` | Conditional branching via `choose if <cond>: <action> [otherwise [if <cond>:] <action>]*` |
| `finish` | Exit listener mode immediately and totally — legal only inside a `when` action block |
| `add` | Append an item to a list |
| `remove` | Retract an item from a list |
| `weakens` | Attach autonomous linear decay to a numeric value — falls to zero over a stated period of ticks |
| `require` | Evaluate a condition; halt with `REQUIREMENT_NOT_MET` on failure (silent on pass) |
| `assign` | Store an item-to-recipient mapping (`assign review-task to "compliance-team"`) |
| `expect` | Evaluate a condition; emit a divergence output line on failure but continue with `SUCCESS` (informational, non-halting) |

### Connectives (18)

| Connective | Purpose |
|---|---|
| `where` | Introduces a filter condition |
| `and` | List construction; compound condition; operation sequencing; record-field continuation; multi-field display in `each ... show` (five contexts, all deterministically disambiguated) |
| `or` | List construction; compound condition; operation sequencing; record-field continuation (four contexts) |
| `from` | Range start; result capture; simple reference; composition parameter declaration and passing |
| `with` | Introduces values, list items, or record fields |
| `called` | Introduces a name |
| `to` | Range endpoint, or component of `equal to`, or recipient in `assign` |
| `how` | Signals a named-composition definition (with `to`) |
| `as` | Field assignment in records |
| `of` | Single-record field access — `<field> of <record>` in any value position |
| `if` | Introduces a `choose` branch's condition |
| `otherwise` | Introduces a `choose` alternative or terminal branch |
| `when` | Registers a reactive handler — top-level only; introduces an indented action block |
| `unless` | Guard clause on a `when` line — compound eligibility is `when-true AND NOT unless-true` |
| `includes` | List membership test in a condition (`where items includes "foo"`) |
| `within` | Numeric tolerance band for the session pack's `measure` verb |
| `over` | Introduces the decay period in `weakens` (`weakens energy over 10`) |
| `then` | Declared sequencing between operations (`add ... then require ...`) — same level as `and` but with stated ordering intent |

### Operators (5)

| Operator | Meaning |
|---|---|
| `is` | Comparison introducer OR equality operator (disambiguated by one-token lookahead) |
| `above` | Strictly greater than |
| `below` | Strictly less than |
| `equal to` | Multi-word operator for explicit equality |
| `not` | Modifier producing distinct semantics — `not above N` is ≤ N (includes the boundary), distinct from `below N` |

### Articles (3)

`the`, `a`, `an`. Decorative — the parser ignores them where they appear.. The articles are decorative Descriptors between an article and `called` (`a domain called X`) are also decorative for semantics but are preserved verbatim in the canonical rendering — your wording reads back the way you wrote it.

### Delimiter (1)

`:` separates a composition name from its body, and a `choose` branch's condition from its action.

### Quoting

`"..."` brackets a multi-word string value or one that would collide with a reserved word (e.g. `with status as "in progress"`, `with label as "filter"`). Quotes are legal in value positions only — names and field names use hyphens for multi-word identifiers (`big-orders`, `start-date`). The renderer's conditional-quoting rule preserves quotes around values that need them and drops them around safe single-word values, so round-trips stay readable.

### v2-deferred (2)

`transform` and `compare` — reserved-word slots protected. The grammar for these verbs is not yet specified; they're reserved so user-provided names won't collide when a future extension lands them.

---

## The pipeline

Liminate has five core processing stages — lexer, reorderer, parser, semantic analyzer, and interpreter — with canonical rendering and structured-result handling around them. Each stage returns data; only the CLI wrapper performs I/O. v3a adds a Phase 2 runtime layer atop this pipeline that activates when `when` blocks register handlers.

### Phase 1 — sequential (v2d-identical)

1. **Lexer.** Splits a line into typed tokens. Case-insensitive; strips decorative punctuation at word edges (interior `.` in `3.14` survives); combines `equal to` into a single operator token via one-word lookahead; recognizes blank lines as no-ops; accumulates `"..."` runs as `QUOTED_STRING` tokens; reports leading-tab indentation as a parse error.

2. **Reorderer.** Narrow table-driven preprocessor that accepts canonical word order, target-before-verb (`the orders filter where ...`), and bare target-before-verb. Other arrangements are rejected with a canonical-form suggestion. The full free-order acceptance is the target state for the tile interface, not the v1 text interpreter.

3. **Parser.** Slot-filling per verb signature. Implements all disambiguation rules — `and`, `or`, `is`, `not`, `to`, `from`, `each` — deterministically via parser state and one-token lookahead. Produces a typed AST. Mixed `and`/`or` in any condition triggers amber-precedence. A second entry point, `parse_when_block(header, action_lines)`, handles indented action blocks: same-depth throughout, deeper-than-block is a parse error, empty blocks are a parse error.

4. **Semantic analyzer.** Checks names against the symbol table, types against operations, field schemas across record lists (every record must have the referenced field), list homogeneity, gather range direction and cap. For named compositions, grammar is validated at definition time and names at call time. v3a extends the analyzer with two listener-aware kwargs (`in_action_block`, `live_value_names`) for the  ownership and `finish`-context rules.

5. **Interpreter.** Executes the validated AST against a mutable symbol table. In-place `filter`, non-destructive `combine`, `gather` stores-and-shows, copy semantics for all data operations, iterator context for `each`, stepwise commit for multi-operation sequences. Phase 1 `WhenNode` statements register into a handler table rather than executing — the action block is parsed but not run until Phase 2.

A thin CLI wrapper is the only module that calls `input()` or `print()`. Every other module returns a structured `LiminateResult`.

### Phase 2 — reactive listener

Phase 2 starts only if Phase 1 completes with zero errors AND at least one `when` handler registered. The runtime then:

1. **Listener entry marker.** Yields a `LISTENING` result with the union of all handler dependency names.

2. **Initial evaluation.** Every registered handler's compound eligibility is evaluated against the current symbol table; any handler that is already eligible fires in registration order with `trigger.source = "initial"`. Cascades resolve depth-first.

3. **Adapter dispatch + event loop.** Each registered domain pack's adapter is attached to the shared, thread-safe event queue and started. The runtime drains one `(name, value)` update at a time to completion — change detection uses deep Liminate value equality, edge-triggered firing on false→true transitions.

4. **Cascading + cycle detection.** Action-block mutations are coalesced by name after the action block completes; modified-name dependents re-evaluate and fire depth-first. The conservative cycle guard rejects same-handler-twice in one cascade chain with `ERROR_RUNTIME`. The handler stays active for future events.

5. **Shutdown.** A `SHUTDOWN` result is yielded when `finish` executes, when all adapters signal completion or fail, or on external termination — with metadata.reason identifying which.

Domain packs are registered externally — either via the CLI `--pack <path>` flag (JSON config) or via the `Session(domain_packs=...)` constructor. v3a ships exactly one adapter (`TestAdapter`) for scripted, deterministic event-driven testing.

---

## Nine outcomes

Every Phase 1 sequential statement produces exactly one of five outcomes:

| Outcome | When | Behavior |
|---|---|---|
| **Success** | Parse + analysis + execution all succeed | Canonical preview displayed; output (if any) written |
| **Amber — precedence** | Mixed `and`/`or` in any `where`/`choose`/`when`/`unless` condition | Parser's interpretation shown with parens; user confirms or restructures |
| **Amber — ambiguity** | Reorderer cannot uniquely resolve slot filling | Clarification prompt; no execution until clarified |
| **Error — parse** | Cannot build an AST (no verb; reserved word in name position; vocabulary word in value position; malformed clause; indentation rule violated) | Plain-English error describing what is missing |
| **Error — semantic** | AST built but references a non-existent name, wrong type, missing field, out-of-range gather, `finish` outside an action block, `remember`/`filter` on a live-value name, etc. | Plain-English error; nothing executed |

Phase 2 listener mode adds four more:

| Outcome | When | Behavior |
|---|---|---|
| **Listening** | Phase 2 begins | One-time entry marker carrying the set of watched names |
| **Handler fire** | An action-block statement runs successfully during firing | Same display shape as Success; wrapped with `trigger` metadata (source, handler index, names changed, new values) |
| **Shutdown** | `finish`, all adapters complete, no adapters registered, or external termination | Terminal result with `reason` metadata |
| **Error — runtime** | Cycle detected (same handler firing twice in one cascade chain), adapter failure, or adapter type mismatch | Plain-English error with `kind` metadata; the handler remains active for future events |

No "warning" category. No silent fallback. The interpreter is deterministic — the prose either runs as written or it doesn't run at all.

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

`count` auto-shows because it is a standalone expression that produces a value. The descriptor `number` between `a` and `called` is decorative — type is inferred from the value.

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

`each` binds an iterator context so `show total` resolves `total` as a field on the current record. Records are copied into the list — mutating `order1` later does not affect `orders[0]`.

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

`filter` modifies `orders` in place. After both filters, only `order1` remains. `show` on a list of records emits one record per line, formatted as `field: value, field: value`.

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

Inside a `where` clause `each` is a pronoun for the current item, not the iteration verb. `combine` is non-destructive, so the final `remember ... from combine the numbers` captures 40 while `numbers` still contains `[6, 7, 8, 9, 10]`. The `from <verb-phrase>` construct triggers recursive descent in the parser.

### Program 5 — the `not` operator

```
gather the scores from 1 to 10
filter the scores where each is not above 7
filter the scores where each is not below 3
filter the scores where each is not equal to 5
```

After all filters, `scores` is `[3, 4, 6, 7]`. `not above 7` means `≤ 7` (the boundary is included), which is distinct from `below 7` which excludes it — `not` is a genuine operator modifier with its own comparison semantics, not a synonym swap.

### Multi-word strings

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

The quoting mechanism is the v2c resolution to D7: values that contain spaces or that collide with reserved words (`"filter"`, `"if"`) wrap in `"..."` and bypass the vocabulary table. Names and field names still use hyphens (`priority-label`, `start-date`) — quotes are value-position only. The renderer drops quotes around single-word non-reserved values to keep round-trips clean.

### Composition parameters + `choose`

```
remember a list called big-orders with order1
remember a list called small-orders with order2
remember how to find-high from data: keep the data where total is above 50

remember the high-from-big called bigwins from find-high from big-orders
remember the high-from-small called smallwins from find-high from small-orders

remember a number called score with 75
choose if score is above 90: show "excellent" otherwise if score is above 50: show "passing" otherwise show "needs work"
```

`find-high` takes one parameter declared with `from <param>` in the definition and passed with `from <name>` at the call site. The composition is reusable on different lists — its body sees `data` bound to the passed list for the duration of the call. `choose` selects the first branch whose condition is true, or the terminal `otherwise` if none match. `if`/`otherwise` are new connectives; the colon is the context switch between condition and action.

### Event-driven listener

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

A `when` line at indent 0 starts an indented action block (min 1 space, tabs rejected, same depth throughout). Each `when` registers a reactive handler; the action block is parsed but not executed during Phase 1. Phase 2 starts after Phase 1 completes with zero errors: handlers fire when their compound eligibility transitions false→true. Updates arrive from an externally-registered domain pack (e.g. `--pack pack.json` for the test adapter). `finish` exits listener mode immediately and totally — no further statements, cascades, or queued updates run after it executes.

Cascades work because action-block writes are watched too: setting `alert-mode` to `on` inside the first handler's action triggers the second handler's eligibility transition. The conservative cycle guard catches genuinely-toggling handler pairs as a runtime error rather than letting them loop.

### Named compositions

```
remember how to find-big-orders: filter the orders where total is above 50
remember how to count-active: filter the orders where status is active and count the orders
```

Stores verb phrases under user-defined names. Calling a composition runs its stored AST against the current symbol table. Names inside the body are resolved at call time, not at definition time — so a composition can reference data that does not yet exist when the composition is defined.

v1 calls a composition by its name alone (e.g. `find-big-orders`). Composition parameters and `from`-chaining are deferred to v2.

### Mixed precedence — amber example

```
filter the orders where total is above 50 and status is active or status is pending
```

The parser deterministically reads this as `(total is above 50 AND status is active) OR status is pending` (standard precedence). Mixed `and`/`or` in a single `where` clause triggers an amber prompt before execution:

> I'll read this as: (total is above 50 and status is active) or status is pending. Is that what you mean? If not, split it into two statements.

The user confirms or rewrites. The parse is unambiguous; the amber exists because non-programmer intuition about boolean precedence is unreliable.

### Stepwise execution

```
remember a list called nums with 1 and 2 and 3 and 4 and 5
filter nums where each is above 3 and show missingname
show nums
```

Line 2 is a two-operation sequence. The filter succeeds and `nums` becomes `[4, 5]` in place. Then `show missingname` fails. The error message names the prior success:

> I completed 'filter the nums where each is above 3' but then I can't find 'missingname'. You might need to 'remember' it first. The filter has already been applied.

Line 3 then shows `4, 5` — the filter's commit persists. Multi-operation sequences are stepwise, not transactional. There is no rollback.

---

## Current scope and deferrals

The shipped build covers v1 (48 locked test sentences) + v2a (11 more) + UX polish + v2.1-patches + v2b (9 more) + v2c (12 more) + v2d (15 more) + v3a (18 more) + v3b (4 more) + v4a (10 more) plus the Metabolic / Normative / Delegated / Epistemic era batches (`weakens`/`over`, `require`/`then`, `assign`/`expect`). **972 tests passing.** Larger scope is intentionally deferred — but the sequential feature set (v1 → v2d), the reactive feature set (v3a/v3b), the pack-verb extension contract, and the era batches together form a structurally complete programming language.

**Currently shipped.** Two-phase execution (Phase 1 sequential, Phase 2 reactive). 21 base verbs. 22 connectives. 58 base reserved words. Self-describing metadata via the Meta-Structural Era's `about` declaration, `because` rationale, and `inherited` provenance modifier (all inert — rendered and inspected, never executed). The Deontic Era's `forbid` (halts with `PROHIBITION_VIOLATED` on a true condition) and `permit` (emits an informational line on a true condition, never halts) completing the require/forbid/permit triangle. The Temporal-Boundary Era's `starting`/`until` statement-initial connectives attaching quoted ISO 8601 effective dates and sunset clauses as inert metadata (temporal evaluation is a product-layer concern, not interpreter runtime). Arithmetic expressions with PEMDAS precedence (`plus`/`minus`/`multiplied by`/`divided by`). In-place list reordering (`sort ... by <field> [in reverse]`). Structured comparison (`compare <left> to <right>` → a `comparison` record). Per-element list mutation (`transform <field> of <list> by <expr>` / `transform <list> by <expr>`). Numbers (integers + decimals). Strings (single-token bare words + multi-word quoted strings via v2c, with verbatim case preservation per). Lists (homogeneous — all numbers, all strings, or all records). Records (named fields, with descriptor preserved on the symbol for pack-verb type checks). Named compositions with optional parameters. Conditional branching via `choose if/otherwise`. In-place `filter`, non-destructive `keep`, non-destructive `combine`, copy semantics, iterator context for `each`, multi-field display in `each ... show`, single-record field access via `show <field> of <record>` and `<field> of <record>` in any value position. Descriptor preservation, named-offender error wording, stepwise sequences. Composition return values via `remember the X from <comp>`. Event-driven `when`/`unless`/`finish` with indented action blocks, single-threaded event queue, edge-triggered evaluation with deep value equality, depth-first cascading with conservative cycle detection, domain-pack adapter contract registered externally via `--pack <path>` JSON or `Session(domain_packs=...)`. v4a general-purpose pack verb contract — packs declare verbs with slot signatures + type constraints + execution dispatch in JSON; the parser dispatches pack verbs after base verbs, the analyzer enforces descriptor-based type constraints, and `set_value` is the first execution type. The UI domain pack ships 10 component nouns and the `navigate to <screen-name>` verb. CLI flags `--quiet`, `--test`, `--pack` (any position).

**Not built (deliberately).** Tile-composition interface. Proposal engine and authorize-don't-author authoring flow. Real-world domain packs (healthcare, smart home, game) — the language ships a test adapter only, packs are product work. Domain pack activation syntax (an Liminate-level `use`/`load` verb). The verbs `transform`, `compare` — reserved-word slots protected, no grammar yet. Symbolic syntax surface. External data sources beyond domain-pack adapters. Negative numbers. Scope isolation beyond the iterator context and composition parameters. Mixed-type lists. Descending ranges. Ranges over 10,000 items. Nested records (and therefore chained `of`). `choose` inside `each`. Sophisticated cycle detection beyond same-handler-twice. Adapter timeout or preemption. Tile interface, proposal engine, domain packs as product surfaces.

The deferrals are not "TODO when we get to it." Each has a specific reason and a documented v2/v3 plan — see [`docs/roadmap/v1-v2-boundary.md`](docs/roadmap/v1-v2-boundary.md) for a readable walkthrough.

---

## Design principles

These are the load-bearing decisions that shape every implementation choice. Each is locked in a specification document and was reaffirmed before any Python was written.

**The prose IS the program.** The interpreter operates exclusively on what the user stated. It does not infer, assume, guess, or fill in unstated information. If the prose doesn't say it, it doesn't happen.

**The vocabulary is the boundary.** 58 reserved words in the current build. v2c added a quoting mechanism for multi-word string values, but only in value positions — names and field names still come from the unquoted name-space. Vocabulary words cannot appear unquoted as user-provided names or as string values. This is structurally why slot-filling parser logic works: every word's category is known in advance. Each addition to the vocabulary (v2a's `keep`, v2a's `of`, v2d's `choose`/`if`/`otherwise`, v3a's `when`/`unless`/`finish`, the `add`/`remove`/`includes`/`within` addenda, Metabolic Era's `weakens`/`over`, Normative Era's `require`/`then`, Delegated/Epistemic Era's `assign`/`expect`, the Infrastructure Era's `by`/`plus`/`minus`/`multiplied by`/`divided by` and `sort`/`reverse`, the V2 promotions `compare`/`transform`, the Meta-Structural Era's `about`/`because`/`inherited`, the Deontic Era's `forbid`/`permit`, and the Temporal-Boundary Era's `starting`/`until`) is the smallest spec change consistent with a dogfooded gap.

**The reorderer does not guess.** When an arrangement of words could fill slots in more than one valid way, the system produces an amber clarification prompt rather than picking one interpretation. Authorship over inference.

**Authorize, don't author.** The on-ramp is modification of a working program, not authorship from a blank file. Programming starts from something that runs.

**Canonical prose rendering as intent verification.** The parser produces a canonical English sentence reconstructed from the AST. The user sees what the parser understood before execution runs — including, critically, on obfuscated or scrambled input. The AST cannot lie.

**Stepwise execution, not transactional.** Multi-operation sequences commit independently. If a later operation fails, earlier side effects remain and the error message names what was completed. The simplest model consistent with sequential interpretation, and matches non-programmer intuition.

**Designed from liberation pedagogy by a non-programmer.** The design origin produces different design decisions at every layer. The vocabulary, the error messages, the verb semantics, the amber-not-error pattern — each one would have been different if a programmer had chosen.

---

## Project structure

```
liminate/
├── CLAUDE.md                        Build instructions for Claude Code
├── README.md                        (this file)
├── pyproject.toml                   Python project config
├── src/liminate/
│   ├── vocabulary.py                Token types, reserved-word sets, verb signatures
│   ├── lexer.py                     Tokenization + `leading_indent`
│   ├── reorderer.py                 Narrow table-driven reorderer
│   ├── parser.py                    Slot-filling parser; AST nodes; `parse_when_block`
│   ├── renderer.py                  AST-to-prose canonical rendering (multi-line for WhenNode)
│   ├── analyzer.py                  Semantic analysis; SymbolEntry; iterator context; v3a `in_action_block` / `live_value_names`
│   ├── interpreter.py               Phase 1 execution; HandlerTable; ContextVars; `_FinishRequested`
│   ├── listener.py                  Phase 2 generator — initial eval, event-queue drain, cascades, cycle detection, shutdown
│   ├── adapter.py                   DomainPack, Adapter, TestAdapter, LiveValueRegistry
│   ├── result.py                    LiminateResult + ResultStatus (9 statuses)
│   ├── cli.py                       Session + REPL + file driver + `--pack` (only module with input/print)
│   └── __main__.py                  `python -m liminate` entry point
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
│   └── conftest.py                  Autouse fixture: resets pack vocabulary between tests
└── examples/
    ├── program1_basics.limn
    ├── program2_orders.limn
    ├── dogfood_*.limn               Per-feature demonstration programs + .actual.txt baselines
    ├── dogfood_v3a_event_driven.limn
    ├── dogfood_v3a_pack.json        Test domain pack for the v3a dogfood
    ├── dogfood_navigate_test.limn   v4a smoke test for `navigate to <screen>`
    └── pack_ui.json                 v4a UI domain pack: 10 nouns + `navigate` verb
```

713 tests pass via `pytest tests/`. Each spec section that locks a behavior has at least one test that exercises it.

---

## The locked test sentences

The test suite is built around locked test sentences that are simultaneously:

- A test case for the lexer, parser, analyzer, and interpreter.
- A grammar artifact — the sentences ARE the discovered grammar; design questions that emerged while writing them became locked resolutions.
- A specification — when the documents and the sentences disagree, the conversation is structured around resolving the inconsistency before any code is written.

Sentence coverage across the test suite:

| Sentences | Coverage |
|---|---|
| 1–30 | The original thirty: every verb in simple + complex forms |
| 32–34 | Reserved-word value position, article `an`, no-verb error |
| 35–48 | Hostile test block — error paths across all categories |
| 49–59 | `keep` basic + capture + composition reuse, `of` field access, multi-field `each show`, composition-chaining error |
| 60–68 | Composition returns, generalized `of` in where/with positions, list-model clarification |
| 69–80 | Quoting mechanism: multi-word values, quoted reserved words, conditional rendering, name/field rejection |
| 81–95 | Composition parameters with `from`, parameterized calls in value-capture position, `choose if`/`otherwise`, multi-statement branches |
| 96–113 | `when` + `unless` + `finish`, initial evaluation, cascades, cycle detection, unset live values, no-adapter shutdown, Phase 1 error blocks Phase 2 |
| 114–117 | Quoted-string case preservation across lex, render, and `where` equality |
| 118–127 | `navigate to <screen>` basic + semantic errors + parse error, UI components with known and freeform fields, `when` on UI components, `navigate` inside an action block, pack-verb reserved-word check, pack noun usable as name without pack |

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
| [`docs/language/syntax.md`](docs/language/syntax.md) | Full syntax tour: source-file rules, all twenty-one verbs, lists, records, conditions, `each`, named compositions with parameters, `choose`, quoting, arithmetic, `sort`/`compare`/`transform`, the Deontic Era's `forbid`/`permit`, the Temporal-Boundary Era's `starting`/`until`, and the v3a `when`/`unless`/`finish` listener model. |
| [`docs/architecture/pipeline.md`](docs/architecture/pipeline.md) | Stage-by-stage walkthrough of how a source line becomes a result, the Phase 2 listener layer for v3a, the nine-outcome trust model, and the I/O boundary. |
| [`docs/roadmap/v1-v2-boundary.md`](docs/roadmap/v1-v2-boundary.md) | What v1 includes and what it intentionally does not, with each deferral framed as a design boundary. |

---

## Lineage

Liminate is the fifth expression of one thesis at different layers:

1. **Narratia.** Educational storytelling. Built on Paulo Freire's pedagogy of the oppressed — learners author their own narratives rather than absorb dominant ones.
2. **Counter-Flow.** A reading-pace experiment. The reader's tempo, not the text's.
3. **TAOS.** Accountability infrastructure. The governed must remain author of the system's accountability.
4. **Möbius Liminate.** A behavioral-rules DSL with prose-as-syntax, tile composition, and authorize-don't-author. The thesis applied to rule authoring within Möbius.
5. **Liminate Programming Language.** The thesis applied to general computation. The same principles, scaled. *(This repository.)*

Each is the same idea — *the person affected must remain the author of their story* — applied to a different layer.

The Möbius Liminate system is a DSL for behavioral rules within Möbius. The Liminate Programming Language is its principles applied to general-purpose computation. They share a lineage and a name; they are not the same system.

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

**Currently shipped.** v1 → v2d (sequential) + v3a/v3b (event-driven listener mode + quoted-string case preservation) + v4a (pack verb contract + UI domain pack) + Metabolic / Normative / Delegated / Epistemic era batches (`weakens`/`over`, `require`/`then`, `assign`/`expect`). 972 tests passing. The interpreter runs in a terminal as text-only, reads `.limn` source files, and offers an interactive REPL with `--quiet`, `--test`, and `--pack` flags. A separate TypeScript port (lexer/reorderer/parser/analyzer/renderer — no interpreter) lives in the Möbius monorepo at `packages/liminate-lang/` and validates the same 127 sentences against this implementation as its sync contract.

**The largest remaining work is not language additions.** It's everything around the language — Future surfaces and domain packs as product surfaces. Specifically:

- **Branch C — Tile interface.** Apply the slot-filling architecture to a visual tile-composition surface with AST-state-filtered tray. The interpreter is the engine; the tile surface is one of three views of the same AST.
- **Branch D — Identity and positioning.** Name decision (Liminate Programming Language vs. a distinct name from Möbius Liminate). Repository setup. License choice. README as manifesto.
- **Branch E — Narratia integration.** The proposal engine that powers "authorize, don't author." Observes intent, proposes a working program for the user to modify.
- **Domain packs as product surfaces.** Healthcare, business, home automation, narrative, legal/compliance. Each pack adds 10–15 context-specific terms plus an adapter implementation. v3a ships only the `TestAdapter` for scripted, deterministic event-driven testing — real-world packs are downstream product work, not language work.

**Smaller language additions still on the deferred list** (in no particular order):

- **`transform` and `compare` verbs.** Reserved-word slots protected through; no grammar yet specified. These would extend the verb set if a dogfooded gap surfaces a clear use case.
- **`choose` inside `each`.** Deferred at; deliberately closed in. The list-level filtering model handles the discriminative cases that motivated it.
- **Sophisticated cycle detection.**'s same-handler-twice guard is conservative — a more nuanced state-based detector could allow legitimately-terminating patterns that the current guard rejects. Deferred until a real use case demands it.
- **Adapter timeout and preemption.**'s single-threaded queue assumes handlers complete quickly. A long-running handler blocks the queue; acceptable for v3a, revisitable later.
- **Domain pack activation via language syntax.** registers packs externally (constructor / CLI). An Liminate-level `use`/`load` verb would let programs declare their adapter dependencies inline.

---

## License

License decision is deferred. Liberation infrastructure should be open from day one; the specific license is a Branch D concern.

---

*Freire said the oppressed must name their own world.*
*A programming language is a tool for naming.*
*The question was never whether non-programmers could think computationally.*
*The question was why we kept handing them someone else's language to do it in.*

*Begin anywhere.*

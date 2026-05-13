# Inscript Programming Language

A prose-as-syntax programming language designed from the human end.

**Status (May 12, 2026):** v1 → v2d (sequential) + v3a (event-driven listener mode) shipped. **641 tests passing.** The sequential feature set (v1 → v2d) and the reactive feature set (v3a) together form a structurally complete programming language.

The interpreter is intentionally bounded: a deterministic text interpreter for sequential rules, data operations, reusable parameterized filters, conditional branching, and reactive handlers driven by external event sources. Not yet the tile interface, the proposal engine, or domain packs as product surfaces — those remain explicitly deferred. Each shipping round resolves dogfooded gaps from the previous one and adds the smallest spec change consistent with the surfaced need — the vocabulary moves from 29 → 34 reserved words across v1 → v3a, not because the language wanted to grow but because dogfooding said it needed to.

---

## Table of contents

- [What it is](#what-it-is)
- [Install and run](#install-and-run)
- [Try this first](#try-this-first)
- [Why it exists](#why-it-exists)
- [What makes it different](#what-makes-it-different)
- [The vocabulary](#the-vocabulary)
- [More examples](#more-examples)
- [The pipeline](#the-pipeline)
- [Nine outcomes](#nine-outcomes)
- [Current scope and deferrals](#current-scope-and-deferrals)
- [Design principles](#design-principles)
- [Project structure](#project-structure)
- [Test discipline](#test-discipline)
- [Guides](#guides)
- [Specification documents](#specification-documents)
- [Lineage](#lineage)
- [Status and what's next](#status-and-whats-next)

---

## What it is

Inscript is an experimental prose-as-syntax programming language whose interpreter executes bounded, readable English programs directly.

`filter the orders where total is above 50` is not a prompt to an AI. It is the program.

A `.insc` source file is plain text — one statement per line. A bounded vocabulary of 34 words combines into sentences that lex, parse, type-check, and execute through a normal compiler pipeline. There is no separate code the prose generates; the sentence IS the program. The long-term thesis is general-purpose computation without leaving readable prose. The current build delivers that foundation across both sequential and reactive execution.

This is not a natural-language layer over Python, not a code-generating AI, and not a domain-specific query language. Inscript has five core processing stages — lexer, reorderer, parser, semantic analyzer, and interpreter — with canonical rendering and structured-result handling around them. v3a adds a Phase 2 reactive runtime that drives registered `when` handlers from an external event source. No `print` calls outside the CLI wrapper.

---

## Install and run

Requires Python 3.10+.

```bash
git clone https://github.com/rmichaelthomas/inscript.git
cd inscript
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

Run the test suite (641 tests, ~0.2 seconds):

```bash
pytest tests/
```

Run a file (Phase 1 sequential):

```bash
python -m inscript examples/program1_basics.insc
```

Run a file with clean output (suppresses the canonical-prose echo):

```bash
python -m inscript --quiet examples/dogfood_v2a_14_realistic.insc
```

Phase 2 listener mode: register `when` handlers in a `.insc` file and drive them with a scripted test domain pack (v3a §118):

```bash
python -m inscript --pack examples/dogfood_v3a_pack.json --test --quiet \
    examples/dogfood_v3a_event_driven.insc
```

Start the interactive REPL (`exit` or `quit` to leave; REPL stays in Phase 1):

```bash
python -m inscript
```

---

## Try this first

Save this as `demo.insc`:

```
gather the numbers from 1 to 10
filter the numbers where each is above 5
combine the numbers
```

Run it:

```bash
python -m inscript demo.insc
```

Expected output (each statement is preceded by the parser's canonical-form preview):

```
I understand this as: gather the numbers from 1 to 10
1, 2, 3, 4, 5, 6, 7, 8, 9, 10
I understand this as: filter the numbers where each is above 5
I understand this as: combine the numbers
40
```

`gather` stores the list and auto-shows it. `filter` modifies it in place. `combine` sums the remaining numbers (6+7+8+9+10 = 40) and auto-shows the result. The "I understand this as" line is the canonical rendering of the parser's AST — the user always sees what the interpreter will run before it runs.

For something larger, try `examples/program1_basics.insc` or `examples/program2_orders.insc`.

---

## Why it exists

Programming languages stand between human intent and computational execution, and they demand the human learn to speak the machine's language. Inscript inverts that: the machine learns to read English.

The intended use cases are practical. **The sequential feature set (v1 → v2d)** targets business rules, legal and regulatory compliance, data filtering and reporting — domains where the person who understands the problem cannot currently express the solution in code. **The reactive feature set (v3a)** extends to healthcare protocols, smart home automation, and narrative scripting — domains where the writer's document could be the program reacting to live changes.

Inscript aims to eliminate the translation step from intent to code by making the readable rule itself executable. The translation step is where errors, cost, and delay concentrate; removing it is a real engineering goal.

---

## What makes it different

Five properties combine in Inscript that exist individually in other systems but never together (inception §7):

1. **Prose-as-syntax where the prose IS the executable code.** Not prose that generates code (Copilot, Cursor). Not prose that describes a game world (Inform 7, which is domain-locked to interactive fiction). Computation expressed as readable English sentences that execute directly.

2. **Bounded vocabulary as design constraint.** 34 reserved words in the current build. The vocabulary is the language boundary, not a starter set that grows. Expressiveness scales through domain packs, composition over expansion, and named-composition chunking — not through adding more keywords. Each addition (v2a's `keep`/`of`, v2d's `choose`/`if`/`otherwise`, v3a's `when`/`unless`/`finish`) is the smallest spec change consistent with a dogfooded gap.

3. **Graduation from tiles to text within one language.** The same AST will underlie a tile-composition surface (for first-encounter authoring), a prose surface (for fluent authoring), and an optional symbolic surface (for velocity). Three views, one structure. Scratch-to-Python is two languages; Inscript is one language with three surfaces. The v1 interpreter implements the prose surface.

4. **Authorize, don't author.** The on-ramp is not a blank file. The system proposes a working program based on observed intent; the human modifies. The first program a user touches is one that already runs. (v1 is the interpreter; the proposal engine is a separate branch.)

5. **Designed from the human end.** Inscript's design started with how a non-programmer would express intent and worked backward to the compiler pipeline, not the other way around. The vocabulary, the error messages, the verb semantics, and the amber-not-error pattern are all consequences of that origin.

---

## The vocabulary

34 reserved words across five categories. No other words are part of the language — only user-provided names and literal values.

### Verbs (10)

| Verb | Purpose |
|---|---|
| `remember` | Store a value, list, record, or named composition (with an optional `from <param>` parameter — v2d §96) |
| `show` | Display a value, an iterator item, a field of a record, or a quoted literal |
| `filter` | Reduce a list in-place by a condition |
| `keep` | Non-destructive sibling of `filter` — returns matches as a fresh list (v2a §67) |
| `count` | Return (and auto-show) the size of a list |
| `gather` | Generate a numeric range, store and auto-show it |
| `combine` | Sum the numbers in a list (non-destructive, auto-shows) |
| `each` | Iterate over a list; sub-action supports multi-field `show A and B` (v2a §69) |
| `choose` | Conditional branching via `choose if <cond>: <action> [otherwise [if <cond>:] <action>]*` (v2d §99) |
| `finish` | Exit listener mode immediately and totally — legal only inside a `when` action block (v3a §112) |

### Connectives (14)

`where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`, `of`, `if`, `otherwise`, `when`, `unless`.

`and` has five distinct meanings (list construction, compound condition, operation sequencing, record-field continuation, multi-field display in `each ... show`) deterministically disambiguated by parser state and one-token lookahead. `or` has the first four. `from` has four contexts including parameter declaration and passing for compositions (v2d §96). `to` is used both as range endpoint and as a component of `equal to`. `of` accesses a single field of a single record in any value position (v2a §68 + v2b §77). `if`/`otherwise` introduce `choose` branches (v2d §99). `when` registers a top-level reactive handler with an indented action block; `unless` is its optional guard clause (v3a §108/§109).

### Operators (5)

`is`, `above`, `below`, `equal to`, `not`.

`is` has dual roles: comparison introducer (`is above 50`) and equality operator (`is active`). `not` is a true modifier — `not above N` means `≤ N` (includes the boundary), distinct from `below N`.

### Articles (3)

`the`, `a`, `an`. Decorative — the parser ignores them.

### Delimiter (1)

`:` separates a composition name from its body, and a `choose` branch's condition from its action.

### Quoting (v2c)

`"..."` brackets a multi-word string value or one that would collide with a reserved word — `with status as "in progress"`, `with label as "filter"`. Quotes are value-position only; names and field names use hyphens. The renderer drops quotes around single-word safe values, so round-trips stay readable. (v2c §86–§92)

### v2-deferred (2)

`transform` and `compare` — reserved-word slots protected. The grammar for these verbs is not yet specified; they're reserved so user-provided names won't collide when (or if) a future addendum lands them.

---

## More examples

The `examples/` directory has two runnable programs. A handful of additional sentences from the locked test suite:

**Records and iteration:**

```
remember an order called order1 with total as 75 and status as active
remember an order called order2 with total as 30 and status as active
remember an order called order3 with total as 120 and status as pending
remember a list called orders with order1 and order2 and order3
each the orders show total
```

Output: `75`, `30`, `120` — one line per record. `each` binds an iterator context so `show total` resolves `total` as a field on the current record.

**Named composition definition + call:**

```
remember how to find-big-orders: filter the orders where total is above 50
find-big-orders
```

Stores a verb phrase under a user-defined name, then calls it. Names inside the body resolve at call time, not at definition time, so a composition can reference data that doesn't yet exist when defined.

**Mixed-precedence amber:**

```
filter the orders where total is above 50 and status is active or status is pending
```

The parser reads this as `(total is above 50 AND status is active) OR status is pending` (standard boolean precedence). Mixed `and`/`or` triggers an amber prompt before execution:

> I'll read this as: (total is above 50 and status is active) or status is pending. Is that what you mean? If not, split it into two statements.

The user confirms or rewrites. The parse is unambiguous; the amber exists because non-programmer intuition about boolean precedence is unreliable.

**Composition parameters + branching (v2d):**

```
remember a list called big-orders with order1
remember how to find-high from data: keep the data where total is above 50
remember the high-from-big called bigwins from find-high from big-orders

remember a number called score with 75
choose if score is above 90: show "excellent" otherwise if score is above 50: show "passing" otherwise show "needs work"
```

`find-high` takes one parameter declared with `from <param>` and passed with `from <name>` at the call site. The composition body sees `data` bound to the caller's argument for the duration of the call. `choose` fires the first branch whose condition is true, or the terminal `otherwise`.

**Event-driven listener (v3a):**

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

A `when` line at indent 0 starts an indented action block (min 1 space, tabs rejected, same depth throughout). Each `when` registers a reactive handler; Phase 2 starts after Phase 1 completes with zero errors. Updates arrive from an externally-registered domain pack. Cascades work because action-block writes are watched: setting `alert-mode` to `on` inside the first handler triggers the second handler's eligibility transition. `finish` exits the listener immediately and totally.

---

## The pipeline

The core pipeline has five processing stages, plus canonical rendering and structured-result handling. Each stage returns data; only the CLI wrapper performs I/O. v3a adds a Phase 2 reactive runtime atop this pipeline that activates when `when` blocks register handlers.

### Phase 1 — sequential

1. **Lexer** — case-insensitive tokenization with edge-stripping of decorative punctuation; combines `equal to` via one-word lookahead; accumulates `"..."` quoted strings (v2c); rejects tab-indented action lines (v3a §110); blank lines are no-ops.

2. **Reorderer** — narrow table-driven preprocessor accepting canonical word order and target-before-verb. Other arrangements reject with a canonical-form suggestion.

3. **Parser** — slot-filling per verb signature. All v1b §44 disambiguation rules resolved by parser state and one-token lookahead. A second entry point handles v3a §110 indented `when` action blocks. Mixed `and`/`or` in any condition triggers amber-precedence.

4. **Semantic analyzer** — names against symbol table, types against operations, field schemas across record lists, list homogeneity, gather range direction and cap. Composition grammar at definition time, names at call time. v3a adds listener-aware kwargs for the §111/§112/§117 ownership and `finish`-context rules.

5. **Interpreter** — in-place `filter`, non-destructive `combine`, `gather` stores-and-shows, copy semantics for all data, iterator context for `each`, stepwise commit for multi-operation sequences. `WhenNode` statements register into a handler table rather than executing.

A thin CLI wrapper is the only module that calls `input()` or `print()`. Every other module returns a structured `InscriptResult`.

### Phase 2 — reactive listener (v3a)

Phase 2 starts only if Phase 1 completes with zero errors AND at least one `when` handler registered. The runtime yields a `LISTENING` marker, runs an initial evaluation (any handler whose compound eligibility is already true fires in registration order), starts the registered domain pack adapters, then drains a single-threaded event queue. Updates trigger edge-triggered firings (false → true transitions only); modifications inside an action block cascade depth-first to dependent handlers; a conservative cycle guard catches genuinely-toggling handler pairs as a runtime error. `finish` is immediate and total — it propagates out of any nesting and yields the terminal `SHUTDOWN` result.

---

## Nine outcomes

Every Phase 1 sequential statement produces exactly one of five outcomes. Phase 2 listener mode adds four more. This is the trust model: no warnings, no silent fallbacks, no fuzzy parsing.

**Phase 1:**

| Outcome | When |
|---|---|
| **Success** | Parse + analysis + execution all succeed |
| **Amber — precedence** | Mixed `and`/`or` in any `where`/`choose`/`when`/`unless` condition |
| **Amber — ambiguity** | Reorderer cannot uniquely resolve slot filling |
| **Error — parse** | Cannot build an AST (includes v3a indentation rule violations) |
| **Error — semantic** | AST built but references a nonexistent name, wrong type, missing field, `finish` outside an action block, `remember`/`filter` on a live-value name, etc. |

**Phase 2 (v3a §122):**

| Outcome | When |
|---|---|
| **Listening** | Phase 2 begins; carries the set of watched names |
| **Handler fire** | An action-block statement runs during firing; wrapped with `trigger` metadata |
| **Shutdown** | `finish`, all adapters complete, no adapters registered, or external termination |
| **Error — runtime** | Cycle detected, adapter failure, adapter type mismatch |

The prose either runs as written, or it doesn't run at all.

---

## Current scope and deferrals

**Currently shipped.** Two-phase execution (Phase 1 sequential, Phase 2 reactive). 10 verbs. 14 connectives. 34 reserved words. Numbers (integers and decimals). Strings (single-token bare words plus multi-word quoted strings via v2c). Lists (homogeneous — numbers, strings, or records). Records (named fields). Named compositions with optional parameters (v2d §96). Conditional branching via `choose if/otherwise` (v2d §99). Composition return values via `remember the X from <comp>` (v2b §76). Generalized `of` (`<field> of <record>` in any value position — v2b §77). In-place `filter`, non-destructive `keep`, non-destructive `combine`, copy semantics, iterator context, multi-field `each show`, descriptor preservation, named-offender error wording, stepwise sequences. Event-driven `when`/`unless`/`finish` with indented action blocks (v3a §110), single-threaded event queue, edge-triggered evaluation with deep value equality, depth-first cascading with conservative cycle detection, domain-pack adapter contract (v3a §116) registered externally. CLI flags `--quiet`, `--test`, `--pack` (any position).

**Not built (deliberately).** Tile-composition interface. Proposal engine and authorize-don't-author authoring flow. Real-world domain packs (healthcare, smart home, game) — language ships a test adapter only; packs are product work. Domain pack activation via Inscript syntax (a `use`/`load` verb). The verbs `transform` and `compare` — reserved-word slots protected, no grammar yet. Symbolic syntax surface. External data sources beyond domain-pack adapters. Negative numbers. Scope isolation beyond the iterator context and composition parameters. Mixed-type lists. Descending ranges. Ranges over 10,000 items. Nested records (and therefore chained `of`). `choose` inside `each`. Sophisticated cycle detection beyond same-handler-twice. Adapter timeout or preemption.

The deferrals are not "TODO when we get to it." Each has a specific reason and a documented plan — see [`docs/roadmap/v1-v2-boundary.md`](docs/roadmap/v1-v2-boundary.md) for a readable walkthrough, or the locked addenda for the source (v1d §66, v2a §75, v2b §84, v2d §103, v3a §126).

---

## Design principles

These are the load-bearing decisions that shape every implementation choice.

- **The prose IS the program.** The interpreter does not infer, assume, or guess. If the prose doesn't say it, it doesn't happen. (v1c §52)
- **The vocabulary is the boundary.** 34 reserved words. v2c added quoting for multi-word string values, but only in value positions — names and field names still come from the unquoted name-space. Vocabulary words cannot appear unquoted as names or as string values. This is structurally why slot-filling parser logic works — every word's category is known in advance. (v1a §29; v1c §46; v2a §73; v2c §86–§92; v3a §124)
- **The reorderer does not guess.** When an arrangement could fill slots in more than one valid way, the system produces an amber clarification prompt rather than picking. Authorship over inference. (inception §17)
- **Authorize, don't author.** The on-ramp is modification of a working program, not authorship from a blank file. (v1a §32)
- **The AST is the source of truth.** The parser produces a canonical English sentence reconstructed from the AST so the user sees what was understood — including, critically, on obfuscated or scrambled input. (v1a §33)
- **Stepwise, not transactional.** Multi-operation sequences commit independently. If a later op fails, earlier side effects remain and the error message names what was completed. (v1d §56)

---

## Project structure

```
inscript/
├── docs/spec/                       Specification documents (immutable)
├── src/inscript/
│   ├── vocabulary.py                Token types, reserved-word sets, verb signatures
│   ├── lexer.py                     Tokenization + leading_indent for v3a action blocks
│   ├── reorderer.py                 Narrow table-driven reorderer
│   ├── parser.py                    Slot-filling parser; AST nodes; parse_when_block
│   ├── renderer.py                  AST-to-prose canonical rendering (multi-line WhenNode)
│   ├── analyzer.py                  Semantic analysis with in_action_block / live_value_names
│   ├── interpreter.py               Phase 1 execution + HandlerTable + ContextVars
│   ├── listener.py                  Phase 2 generator — initial eval, cascades, cycle detection, shutdown
│   ├── adapter.py                   DomainPack, Adapter, TestAdapter, LiveValueRegistry
│   ├── result.py                    InscriptResult + ResultStatus (9 statuses)
│   ├── cli.py                       Session + REPL + file driver + --pack (the only I/O boundary)
│   └── __main__.py                  `python -m inscript` entry point
├── tests/                           Per-stage tests + integration suites for all 113 sentences
└── examples/
    ├── program1_basics.insc
    ├── program2_orders.insc
    ├── dogfood_*.insc               Per-addendum dogfood programs
    ├── dogfood_v3a_event_driven.insc
    └── dogfood_v3a_pack.json        Test domain pack for the v3a dogfood
```

---

## Test discipline

The test suite is built around locked test sentences that accumulate across addenda — 48 from v1 (34 success + 14 hostile), 11 from v2a §74, 9 from v2b §83, 12 from v2c §94, 15 from v2d §105, and 18 from v3a §125. **113 sentences total.**

Each sentence is simultaneously a test case for every pipeline stage and a grammar artifact: the sentences ARE the discovered grammar. Design questions that surface while writing them get resolved in the specification before any Python is written. The rhythm is *write the sentences → resolve the questions → implement → dogfood the result*.

641 tests run in ~0.2 seconds. Every spec section that locks a behavior has at least one test exercising it.

---

## Guides

Human-readable guides live under `docs/`. They are derived from the
locked specifications but written for fluent reading rather than
authority.

| Guide | What it covers |
|---|---|
| [`docs/language/quickstart.md`](docs/language/quickstart.md) | Install, run tests, run an example, start the REPL, and try a three-line demo program. |
| [`docs/language/syntax.md`](docs/language/syntax.md) | Full syntax tour: source-file rules, all ten verbs, lists, records, conditions, `each`, named compositions with parameters, `choose`, quoting, and the v3a `when`/`unless`/`finish` listener model. |
| [`docs/architecture/pipeline.md`](docs/architecture/pipeline.md) | Stage-by-stage walkthrough of how a source line becomes a result, the Phase 2 listener layer for v3a, the nine-outcome trust model, and the I/O boundary. |
| [`docs/roadmap/v1-v2-boundary.md`](docs/roadmap/v1-v2-boundary.md) | What v1 includes and what it intentionally does not, with each deferral framed as a design boundary. |

The guides cross-link each other and point back to `docs/spec/` when
the precise wording matters.

---

## Specification documents

The build specification grows by addendum. Earlier documents are never overwritten — additions extend the section numbering.

| Document | Status |
|---|---|
| `inscript_inception_checkpoint_v1.md` | Locked + implemented |
| `inscript_addendum_v1a_pre_build.md` | Locked + implemented |
| `inscript_addendum_v1b_design_resolutions.md` | Locked + implemented |
| `inscript_addendum_v1c_implementation_hardening.md` | Locked + implemented |
| `inscript_addendum_v1d_build_boundary.md` | Locked + implemented |
| `inscript_addendum_v2a_dogfooding_resolutions.md` | Locked + implemented: `keep` verb, `of` connective, multi-field `each show`, descriptor preservation |
| `inscript_addendum_v2b_composition_returns.md` | Locked + implemented: composition return values, generalized `of` |
| `inscript_addendum_v2c_multi_word_strings.md` | Locked + implemented: quoting mechanism for multi-word string values |
| `inscript_addendum_v2d_parameters_and_branching.md` | Locked + implemented: composition parameters with `from`, `choose` verb with `if`/`otherwise` |
| `inscript_addendum_v3a_event_driven_execution.md` | Locked + implemented: two-phase execution, `when`/`unless`/`finish`, indentation-based action blocks, adapter contract, cascading triggers with cycle detection |
| `inscript_v1_thirty_sentences.md` | Test specification: 113 sentences (30 + v1c §53 + v1d §65 + v2a §74 + v2b §83 + v2c §94 + v2d §105 + v3a §125) |

The spec documents are immutable build artifacts. The code is built against them, not the other way around. Two triage documents and two gap inventories under `docs/` show how each addendum was scoped against dogfooding evidence.

---

## Lineage

Inscript is the fifth in a sequence of projects applying one thesis at different layers — *the person affected must remain the author of their story*.

- **Narratia.** Educational storytelling. Built on Paulo Freire's pedagogy of the oppressed — learners author their own narratives rather than absorb dominant ones.
- **Counter-Flow.** A reading-pace experiment. The reader's tempo, not the text's.
- **TAOS.** Accountability infrastructure. The governed remain author of the system's accountability.
- **Möbius Inscript.** A behavioral-rules DSL with prose-as-syntax, tile composition, and authorize-don't-author. The thesis applied to rule authoring within Möbius.
- **Inscript Programming Language.** The thesis applied to general computation. *(This repository.)*

Möbius Inscript and this Inscript Programming Language share a lineage and a name; they are not the same system.

---

## Status and what's next

**Currently shipped.** v1 → v2d (sequential) + v3a (event-driven listener mode). 641 tests passing. The interpreter runs in a terminal, reads `.insc` source files, and offers an interactive REPL with `--quiet`, `--test`, and `--pack` flags. The sequential and reactive feature sets together form a structurally complete programming language.

**The largest remaining work is not language additions.** It's everything around the language:

- **Tile interface** — apply slot-filling to a visual tile-composition surface (one of three views of the same AST).
- **Narratia integration** — the proposal engine that powers "authorize, don't author."
- **Domain packs as product surfaces** — healthcare, business, home automation, narrative, legal/compliance. v3a ships only the `TestAdapter` for scripted event-driven testing; real-world packs are downstream product work.
- **Identity and positioning** — name decision, repository setup, license choice.

**Smaller language additions still deferred** include the verbs `transform` and `compare` (reserved-word slots protected, no grammar yet), `choose` inside `each`, domain pack activation via an Inscript `use`/`load` verb, sophisticated cycle detection beyond same-handler-twice, and adapter timeout/preemption.

---

## License

License decision is deferred. Liberation infrastructure should be open from day one; the specific choice is part of the Identity-and-Positioning branch.

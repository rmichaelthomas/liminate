# Inscript Programming Language

A prose-as-syntax programming language designed from the human end.

**Status:** v1 interpreter — feature-complete. 385 tests passing. All 48 locked test sentences executed end-to-end.

v1 is intentionally small: it is a deterministic text interpreter for sequential rules and data operations, not yet the tile interface, proposal engine, or event-driven system.

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
- [Five outcomes](#five-outcomes)
- [v1 scope and v2 deferrals](#v1-scope-and-v2-deferrals)
- [Design principles](#design-principles)
- [Project structure](#project-structure)
- [Test discipline](#test-discipline)
- [Guides](#guides)
- [Specification documents](#specification-documents)
- [Lineage](#lineage)
- [Status and what's next](#status-and-whats-next)

---

## What it is

Inscript is an experimental prose-as-syntax programming language whose v1 interpreter executes bounded, readable English programs directly.

`filter the orders where total is above 50` is not a prompt to an AI. It is the program.

A `.insc` source file is plain text — one statement per line. A bounded vocabulary of 29 words combines into sentences that lex, parse, type-check, and execute through a normal compiler pipeline. There is no separate code the prose generates; the sentence IS the program. The long-term thesis is general-purpose computation without leaving readable prose. v1 is the deterministic starting point.

This is not a natural-language layer over Python, not a code-generating AI, and not a domain-specific query language. Inscript has its own lexer, reorderer, parser, semantic analyzer, and interpreter — five stages that return structured results, no `print` calls outside the CLI wrapper.

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

Run the test suite (385 tests, ~0.2 seconds):

```bash
pytest tests/
```

Run a file:

```bash
python -m inscript examples/program1_basics.insc
```

Start the interactive REPL (`exit` or `quit` to leave):

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

The intended use cases are practical. **v1 targets sequential rules**: business rules, legal and regulatory compliance, data filtering and reporting — domains where the person who understands the problem cannot currently express the solution in code. **v2 (event-driven, deferred)** extends to healthcare protocols, smart home automation, and narrative scripting — domains where the writer's document could be the program.

Inscript aims to eliminate the translation step from intent to code by making the readable rule itself executable. In v1, that begins with sequential business rules, compliance logic, and data filtering. The translation step is where errors, cost, and delay concentrate; removing it is a real engineering goal.

---

## What makes it different

Five properties combine in Inscript that exist individually in other systems but never together (inception §7):

1. **Prose-as-syntax where the prose IS the executable code.** Not prose that generates code (Copilot, Cursor). Not prose that describes a game world (Inform 7, which is domain-locked to interactive fiction). Computation expressed as readable English sentences that execute directly.

2. **Bounded vocabulary as design constraint.** 29 reserved words in v1. The vocabulary is the language boundary, not a starter set that grows. Expressiveness scales through domain packs, composition over expansion, and named-composition chunking — not through adding more keywords.

3. **Graduation from tiles to text within one language.** The same AST will underlie a tile-composition surface (for first-encounter authoring), a prose surface (for fluent authoring), and an optional symbolic surface (for velocity). Three views, one structure. Scratch-to-Python is two languages; Inscript is one language with three surfaces. The v1 interpreter implements the prose surface.

4. **Authorize, don't author.** The on-ramp is not a blank file. The system proposes a working program based on observed intent; the human modifies. The first program a user touches is one that already runs. (v1 is the interpreter; the proposal engine is a separate branch.)

5. **Designed from the human end.** Inscript's design started with how a non-programmer would express intent and worked backward to the compiler pipeline, not the other way around. The vocabulary, the error messages, the verb semantics, and the amber-not-error pattern are all consequences of that origin.

---

## The vocabulary

29 reserved words across five categories. No other words are part of v1 — only user-provided names and literal values.

### Verbs (7)

| Verb | Purpose |
|---|---|
| `remember` | Store a value, list, record, or named composition |
| `show` | Display the value of a named item or the current iterator item |
| `filter` | Reduce a list in-place by a condition |
| `count` | Return (and auto-show) the size of a list |
| `gather` | Generate a numeric range, store and auto-show it |
| `combine` | Sum the numbers in a list (non-destructive, auto-shows) |
| `each` | Iterate over a list and perform an action per item |

### Connectives (9)

`where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`.

`and`/`or` have four distinct meanings (list construction, compound condition, operation sequencing, record-field continuation) deterministically disambiguated by parser state and one-token lookahead. `from` has three contexts. `to` is used both as range endpoint and as a component of `equal to`.

### Operators (5)

`is`, `above`, `below`, `equal to`, `not`.

`is` has dual roles: comparison introducer (`is above 50`) and equality operator (`is active`). `not` is a true modifier — `not above N` means `≤ N` (includes the boundary), distinct from `below N`.

### Articles (3)

`the`, `a`, `an`. Decorative — the parser ignores them.

### Delimiter (1)

`:` separates a composition name from its body.

### v2-reserved (5)

`when`, `unless`, `transform`, `choose`, `compare` — designed but not executable in v1. Reserved now so user-provided names don't break when v2 ships.

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

---

## The pipeline

Five stages, each returning structured results.

1. **Lexer** — case-insensitive tokenization with edge-stripping of decorative punctuation; combines `equal to` via one-word lookahead; blank lines are no-ops.

2. **Reorderer** — narrow table-driven preprocessor accepting canonical word order and target-before-verb. Other arrangements reject with a canonical-form suggestion. (Full free-order acceptance is for the tile interface, not the v1 text interpreter.)

3. **Parser** — slot-filling per verb signature. All seven disambiguation rules (`and`, `or`, `is`, `not`, `to`, `from`, `each`) resolved by parser state and one-token lookahead. Mixed `and`/`or` in a single `where` clause triggers amber-precedence.

4. **Semantic analyzer** — names against symbol table, types against operations, field schemas across record lists, list homogeneity, gather range direction and cap. Composition grammar at definition time, names at call time.

5. **Interpreter** — in-place `filter`, non-destructive `combine`, `gather` stores-and-shows, copy semantics for all data, iterator context for `each`, stepwise commit for multi-operation sequences (a later failure does not roll back earlier side effects).

A thin CLI wrapper is the only module that calls `input()` or `print()`. Every other module returns a structured `InscriptResult`.

---

## Five outcomes

Every statement produces exactly one of five outcomes. This is the trust model: no warnings, no silent fallbacks, no fuzzy parsing.

| Outcome | When |
|---|---|
| **Success** | Parse + analysis + execution all succeed |
| **Amber — precedence** | Mixed `and`/`or` in a single `where` clause |
| **Amber — ambiguity** | Reorderer cannot uniquely resolve slot filling |
| **Error — parse** | Cannot build an AST |
| **Error — semantic** | AST built but references a nonexistent name, wrong type, missing field, or out-of-range gather |

The prose either runs as written, or it doesn't run at all.

---

## v1 scope and v2 deferrals

**v1 includes.** Sequential execution. 7 verbs. 29 reserved words. Numbers (integers and decimals). Strings (single-token bare words). Lists (homogeneous — all numbers, all strings, or all records). Records (named fields). Named compositions. In-place `filter`, non-destructive `combine`, copy semantics, iterator context, stepwise sequences.

**v1 does not include.** Tile-composition interface. Proposal engine and authorize-don't-author authoring flow. Domain packs. Event-driven execution (`when`/`unless`). The verbs `transform`, `choose`, `compare`. Symbolic syntax surface. External data sources (databases, APIs). Multi-word strings (no quoting). Composition parameters. Negative numbers. Scope isolation beyond the iterator context. Mixed-type lists. Descending ranges. Ranges over 10,000 items.

The deferrals are not "TODO when we get to it." Each has a specific reason and a documented v2 grammar plan — see [`docs/roadmap/v1-v2-boundary.md`](docs/roadmap/v1-v2-boundary.md) for a readable walkthrough, or `docs/spec/inscript_addendum_v1d_build_boundary.md` §66 for the locked source.

---

## Design principles

These are the load-bearing decisions that shape every implementation choice.

- **The prose IS the program.** The interpreter does not infer, assume, or guess. If the prose doesn't say it, it doesn't happen. (v1c §52)
- **The vocabulary is the boundary.** 29 reserved words. No quoting mechanism. Vocabulary words cannot appear as names or string values. This is structurally why slot-filling parser logic works — every word's category is known in advance. (v1a §29; v1c §46)
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
│   ├── lexer.py                     Tokenization
│   ├── reorderer.py                 Narrow table-driven reorderer
│   ├── parser.py                    Slot-filling parser; AST node types; TokenStream
│   ├── renderer.py                  AST-to-prose canonical rendering
│   ├── analyzer.py                  Semantic analysis; SymbolEntry; iterator context
│   ├── interpreter.py               Execution engine with copy semantics
│   ├── result.py                    InscriptResult + ResultStatus
│   ├── cli.py                       REPL + file driver (the only I/O boundary)
│   └── __main__.py                  `python -m inscript` entry point
├── tests/                           Phase 1–7 tests; integration covers all 48 sentences
└── examples/
    ├── program1_basics.insc
    └── program2_orders.insc
```

---

## Test discipline

The test suite is built around 48 locked test sentences — 34 success cases and 14 hostile cases (reserved-word violations, missing names, type errors, mixed-type lists, descending ranges, range cap, missing fields, malformed records, stepwise-failure context).

Each sentence is simultaneously a test case for every pipeline stage and a grammar artifact: the sentences ARE the discovered grammar. Eight design questions surfaced while writing them and were resolved in the specification before any Python was written.

385 tests run in ~0.2 seconds. Every spec section that locks a behavior has at least one test exercising it.

---

## Guides

Human-readable guides live under `docs/`. They are derived from the
locked specifications but written for fluent reading rather than
authority.

| Guide | What it covers |
|---|---|
| [`docs/language/quickstart.md`](docs/language/quickstart.md) | Install, run tests, run an example, start the REPL, and try a three-line demo program. |
| [`docs/language/syntax.md`](docs/language/syntax.md) | Full v1 syntax tour: source-file rules, all seven verbs, lists, records, conditions, `each`, named compositions, and the v1 limits. |
| [`docs/architecture/pipeline.md`](docs/architecture/pipeline.md) | Stage-by-stage walkthrough of how a source line becomes a result, plus the five-outcome trust model and the I/O boundary. |
| [`docs/roadmap/v1-v2-boundary.md`](docs/roadmap/v1-v2-boundary.md) | What v1 includes and what it intentionally does not, with each deferral framed as a design boundary. |

The guides cross-link each other and point back to `docs/spec/` when
the precise wording matters.

---

## Specification documents

Five documents constitute the v1 build specification, plus the test spec. Earlier documents are never overwritten — additions extend the section numbering.

| Document | Locks |
|---|---|
| `inscript_inception_checkpoint_v1.md` | Vocabulary, pipeline, verb signatures, parser rules, interpreter behaviors, v1/v2 scope |
| `inscript_addendum_v1a_pre_build.md` | Reserved-word exclusion, mixed-precedence amber, canonical prose rendering, tile-tray filtering, authorize-don't-author constraint |
| `inscript_addendum_v1b_design_resolutions.md` | Eight design resolutions; complete parser disambiguation ruleset |
| `inscript_addendum_v1c_implementation_hardening.md` | Vocabulary-words-can't-be-values, article `an`, blank-line handling, iterator context, output taxonomy, parser lookahead, deterministic interpretation |
| `inscript_addendum_v1d_build_boundary.md` | Reorderer scope, stepwise execution, case normalization, duplicate overwrite, homogeneous lists, schema homogeneity, single-token strings, descending ranges, range cap, structured results, build boundary |
| `inscript_v1_thirty_sentences.md` | 48 test sentences (30 + 4 + 14) |

The spec documents are immutable build artifacts. The code is built against them, not the other way around.

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

**v1 interpreter is complete.** 385 tests passing. All 48 locked sentences exercised. The interpreter runs in a terminal, reads `.insc` source files, and offers an interactive REPL.

Next branches (in no particular order):

- **Tile interface** — apply slot-filling to a visual tile-composition surface (one of three views of the same AST).
- **Narratia integration** — the proposal engine that powers "authorize, don't author."
- **v2 event-driven execution** — `when`/`unless` and a listener model for healthcare protocols, smart home automation, reactive game logic.
- **Domain packs** — healthcare, business, home automation, narrative, legal/compliance.
- **v2 verbs** — `transform`, `choose`, `compare` with fully specified grammars.

---

## License

License decision is deferred. Liberation infrastructure should be open from day one; the specific choice is part of the Identity-and-Positioning branch.

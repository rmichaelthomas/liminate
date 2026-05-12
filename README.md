# Inscript Programming Language

A prose-as-syntax programming language designed from the human end.

> *"Every programming language in history was designed by programmers. This one wasn't. That's why the design is different."*
> — Inscript Inception Checkpoint v1

**Status:** v1 interpreter — feature-complete. 385 tests passing. All 48 locked test sentences executed end-to-end.

---

## Table of contents

- [What it is](#what-it-is)
- [Why it exists](#why-it-exists)
- [What makes it different](#what-makes-it-different)
- [Quick example](#quick-example)
- [Installation and running](#installation-and-running)
- [The vocabulary](#the-vocabulary)
- [The pipeline](#the-pipeline)
- [Five outcomes](#five-outcomes)
- [Example programs](#example-programs)
- [v1 scope and v2 deferrals](#v1-scope-and-v2-deferrals)
- [Design principles](#design-principles)
- [Project structure](#project-structure)
- [The forty-eight test sentences](#the-forty-eight-test-sentences)
- [Specification documents](#specification-documents)
- [Lineage](#lineage)
- [Architects and builders](#architects-and-builders)
- [Status and what's next](#status-and-whats-next)

---

## What it is

`filter the orders where total is above 50` is not a prompt to an AI. It is the program.

Inscript is a general-purpose programming language whose source code is readable English prose. A bounded vocabulary of 29 words combines into sentences that execute directly. There is no separate code the prose generates — the sentence IS the program.

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

2. **Bounded vocabulary as design constraint.** 29 reserved words in v1. The vocabulary is the language boundary, not a starter set that grows. Expressiveness scales through domain packs, composition over expansion, and named-composition chunking (inception §19) — not through adding more keywords.

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

Every statement is echoed first in canonical prose form (the parser's interpretation of what you wrote) before any output is shown. This is the "Logic Preview" — see v1a §33.

---

## The vocabulary

The v1 vocabulary is 29 reserved words across five categories. The complete list is the entire language surface — no other words are part of Inscript v1, only user-provided names and literal values.

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

| Connective | Purpose |
|---|---|
| `where` | Introduces a filter condition |
| `and` | List construction; compound condition; operation sequencing; record-field continuation (four contexts, all deterministically disambiguated) |
| `or` | Same four contexts as `and` |
| `from` | Range start; result capture; simple reference (three contexts) |
| `with` | Introduces values, list items, or record fields |
| `called` | Introduces a name |
| `to` | Range endpoint, or component of `equal to` |
| `how` | Signals a named-composition definition (with `to`) |
| `as` | Field assignment in records |

### Operators (5)

| Operator | Meaning |
|---|---|
| `is` | Comparison introducer OR equality operator (disambiguated by one-token lookahead) |
| `above` | Strictly greater than |
| `below` | Strictly less than |
| `equal to` | Multi-word operator for explicit equality |
| `not` | Modifier producing distinct semantics — `not above N` is ≤ N (includes the boundary), distinct from `below N` (§21 line 416) |

### Articles (3)

`the`, `a`, `an`. Decorative — the parser ignores them where they appear. (Including `an` is v1c §47; the inception checkpoint originally listed only `the` and `a`.)

### Delimiter (1)

`:` separates a composition name from its body.

### v2-reserved (5)

`when`, `unless`, `transform`, `choose`, `compare` — designed but not executable in v1. Reserved now so user-provided names don't break when v2 ships (v1a §29).

---

## The pipeline

Five stages, each returning structured results. No direct I/O until the CLI wrapper (v1d §64).

1. **Lexer.** Splits a line into typed tokens. Case-insensitive; strips decorative punctuation at word edges (interior `.` in `3.14` survives); combines `equal to` into a single operator token via one-word lookahead; recognizes blank lines as no-ops. (inception §22; v1c §47–§48)

2. **Reorderer.** Narrow table-driven preprocessor that accepts canonical word order, target-before-verb (`the orders filter where ...`), and bare target-before-verb. Other arrangements are rejected with a canonical-form suggestion. The full free-order acceptance is the target state for the tile interface, not the v1 text interpreter. (v1d §55)

3. **Parser.** Slot-filling per verb signature. Implements all seven disambiguation rules from v1b §44 — `and`, `or`, `is`, `not`, `to`, `from`, `each` — deterministically via parser state and one-token lookahead. Produces a typed AST. Mixed `and`/`or` in a single `where` clause triggers an amber-precedence outcome with a parenthesized message showing the parser's interpretation. (inception §21; v1a §30; v1b §44; v1c §51)

4. **Semantic analyzer.** Checks names against the symbol table, types against operations, field schemas across record lists (every record must have the referenced field, v1d §60), list homogeneity (v1d §59), gather range direction and cap (v1d §62/§63). For named compositions, grammar is validated at definition time and names at call time (§23 line 466).

5. **Interpreter.** Executes the validated AST against a mutable symbol table. In-place `filter`, non-destructive `combine`, `gather` stores-and-shows, copy semantics for all data operations, iterator context for `each`, stepwise commit for multi-operation sequences (a later failure does not roll back earlier side effects). (§24; v1b §38–§42; v1c §49; v1d §56–§58)

A thin CLI wrapper is the only module that calls `input()` or `print()`. Every other module returns a structured `InscriptResult`. (v1d §64)

---

## Five outcomes

Every statement produces exactly one of five outcomes (v1c §50):

| Outcome | When | Behavior |
|---|---|---|
| **Success** | Parse + analysis + execution all succeed | Canonical preview displayed; output (if any) written |
| **Amber — precedence** | Mixed `and`/`or` in a single `where` clause | Parser's interpretation shown with parens; user confirms or restructures |
| **Amber — ambiguity** | Reorderer cannot uniquely resolve slot filling | Clarification prompt; no execution until clarified |
| **Error — parse** | Cannot build an AST (no verb; reserved word in name position; vocabulary word in value position; malformed clause) | Plain-English error describing what is missing |
| **Error — semantic** | AST built but references a non-existent name, wrong type, missing field, out-of-range gather, etc. | Plain-English error; nothing executed |

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

## v1 scope and v2 deferrals

The v1 interpreter passes all 48 locked test sentences. Larger scope is intentionally deferred.

**v1 is.** Sequential execution. 7 verbs. 29 reserved words. Numbers (integers + decimals). Strings (single-token bare words). Lists (homogeneous — all numbers, all strings, or all records). Records (named fields). Named compositions. In-place filter, non-destructive combine, copy semantics, iterator context for `each`, stepwise sequences.

**v1 is NOT.** Tile-composition interface. Proposal engine and authorize-don't-author authoring flow. Domain packs. Event-driven execution (`when`/`unless`). The verbs `transform`, `choose`, `compare`. Symbolic syntax surface. External data sources. Multi-word strings (no quoting in v1). Composition parameters. Negative numbers. Scope isolation beyond the iterator context. Mixed-type lists. Descending ranges. Ranges over 10,000 items.

The deferrals are not "TODO when we get to it." Each has a specific reason and a documented v2 grammar plan — see `docs/spec/inscript_addendum_v1d_build_boundary.md` §66.

---

## Design principles

These are the load-bearing decisions that shape every implementation choice. Each is locked in a specification document and was reaffirmed before any Python was written.

**The prose IS the program.** The interpreter operates exclusively on what the user stated. It does not infer, assume, guess, or fill in unstated information. If the prose doesn't say it, it doesn't happen. (v1c §52)

**The vocabulary is the boundary.** 29 reserved words in v1. No quoting mechanism. Vocabulary words cannot appear as user-provided names or as string values. This is structurally why slot-filling parser logic works: every word's category is known in advance. (v1a §29; v1c §46)

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
├── BUILD_PLAN.md                    Seven-phase build plan
├── README.md                        (this file)
├── pyproject.toml                   Python project config
├── docs/spec/                       Specification documents (immutable)
│   ├── inscript_inception_checkpoint_v1.md
│   ├── inscript_addendum_v1a_pre_build.md
│   ├── inscript_addendum_v1b_design_resolutions.md
│   ├── inscript_addendum_v1c_implementation_hardening.md
│   ├── inscript_addendum_v1d_build_boundary.md
│   └── inscript_v1_thirty_sentences.md
├── src/inscript/
│   ├── vocabulary.py                Token types, reserved-word sets, verb signatures
│   ├── lexer.py                     Tokenization
│   ├── reorderer.py                 Narrow table-driven reorderer
│   ├── parser.py                    Slot-filling parser; AST node types; TokenStream
│   ├── renderer.py                  AST-to-prose canonical rendering
│   ├── analyzer.py                  Semantic analysis; SymbolEntry; iterator context
│   ├── interpreter.py               Execution engine with copy semantics
│   ├── result.py                    InscriptResult + ResultStatus
│   ├── cli.py                       REPL + file driver (only module with input/print)
│   └── __main__.py                  `python -m inscript` entry point
├── tests/
│   ├── test_vocabulary.py           Phase 1
│   ├── test_result.py               Phase 1
│   ├── test_lexer.py                Phase 2
│   ├── test_reorderer.py            Phase 3
│   ├── test_parser.py               Phase 4
│   ├── test_renderer.py             Phase 4
│   ├── test_analyzer.py             Phase 5
│   ├── test_interpreter.py          Phase 6
│   ├── test_integration.py          Phase 7 — all 48 sentences end-to-end
│   └── conftest.py
└── examples/
    ├── program1_basics.insc
    └── program2_orders.insc
```

385 tests pass via `pytest tests/`. Each spec section that locks a behavior has at least one test that exercises it.

---

## The forty-eight test sentences

The test suite is built around 48 locked test sentences from `docs/spec/inscript_v1_thirty_sentences.md` plus v1c §53 (sentences 32–34) and v1d §65 (sentences 35–48). Each sentence is simultaneously:

- A test case for the lexer, parser, analyzer, and interpreter.
- A grammar artifact — the sentences ARE the discovered grammar; design questions that emerged while writing them are the eight resolutions in v1b §36–§43.
- A specification — when the documents and the sentences disagree, the conversation is structured around resolving the inconsistency before any code is written.

Of the 48:

- **34 are success cases.** They parse, validate, and execute to specific outputs and symbol-table states.
- **14 are hostile cases.** They exercise the error paths: reserved word violations, missing names, type errors, mixed-type lists, descending ranges, range cap exceeded, missing fields on records, malformed records, stepwise-failure context messages.

Every sentence is exercised end-to-end in `tests/test_integration.py`.

---

## Specification documents

Five documents constitute the v1 build specification, plus the test spec. Each new document either locks new decisions or closes gaps surfaced by external review of the previous ones. Earlier documents are never overwritten — additions extend the section numbering.

| Document | Locks |
|---|---|
| `inscript_inception_checkpoint_v1.md` | Vocabulary (§11), pipeline (§8–§9), verb signatures (§17), parser rules (§21–§22), interpreter behaviors (§24), v1/v2 scope (§25) |
| `inscript_addendum_v1a_pre_build.md` | Reserved-word exclusion (§29), mixed-precedence amber (§30), AST-state-filtered tile tray (§31), authorization-requires-compositional-act (§32), canonical prose rendering (§33) |
| `inscript_addendum_v1b_design_resolutions.md` | Eight design resolutions surfaced by the thirty test sentences (§36–§43); complete parser disambiguation ruleset (§44) |
| `inscript_addendum_v1c_implementation_hardening.md` | Vocabulary words can't be values (§46), article `an` (§47), blank-line handling (§48), iterator context (§49), output taxonomy (§50), parser lookahead capability (§51), deterministic interpretation (§52) |
| `inscript_addendum_v1d_build_boundary.md` | Reorderer v1 scope (§55), stepwise execution (§56), case normalization (§57), duplicate overwrite (§58), homogeneous lists (§59), record schema homogeneity (§60), single-token strings (§61), descending ranges (§62), gather range cap (§63), structured results (§64), build boundary (§66) |
| `inscript_v1_thirty_sentences.md` | Test specification: 30 + 4 (v1c §53) + 14 (v1d §65) = 48 sentences |

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
| v1 interpreter builder | Claude Code |
| v1 build session | May 11–12, 2026 |

The build was a paired collaboration. The architect produced and approved every design decision in the locked specification documents. The builder translated those decisions into Python — and, when implementation surfaced an ambiguity, opened the spec document rather than guessing. The CLAUDE.md rule: every claim is load-bearing; do not state that a spec section says something without verifying.

---

## Status and what's next

**v1 interpreter: complete.** 385 tests passing. All 48 locked sentences exercised. The interpreter runs in a terminal as text-only, reads `.insc` source files, and offers an interactive REPL.

**Next, in no particular order** (from inception §27, Branches for Future Sessions):

- **Branch C — Tile interface.** Apply the slot-filling architecture to a visual tile-composition surface with AST-state-filtered tray (v1a §31). The interpreter is the engine; the tile surface is one of three views of the same AST.
- **Branch D — Identity and positioning.** Name decision (Inscript Programming Language vs. a distinct name from Möbius Inscript). Repository setup. License choice. README as manifesto.
- **Branch E — Narratia integration.** The proposal engine that powers "authorize, don't author." Observes intent, proposes a working program for the user to modify.
- **Branch F — v2 event-driven execution.** Adds `when` and `unless` and a listener model. Required for healthcare protocols, smart home automation, and reactive game logic.
- **Domain packs.** Healthcare, business, home automation, narrative, legal/compliance. Each pack adds 10–15 context-specific terms (inception §19).
- **v2 verbs.** `transform`, `choose`, `compare` — designed but with under-specified semantics that need additional grammar before they execute.

---

## License

License decision is deferred — see inception §26 open question Q10. Liberation infrastructure should be open from day one; the specific license is a Branch D concern.

---

*Freire said the oppressed must name their own world.*
*A programming language is a tool for naming.*
*The question was never whether non-programmers could think computationally.*
*The question was why we kept handing them someone else's language to do it in.*

*Begin anywhere.*

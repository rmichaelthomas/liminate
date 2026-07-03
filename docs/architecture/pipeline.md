# Pipeline architecture

A guide to how Liminate turns a source line — or a whole listener-mode
program — into a result. This document walks the stages in plain
English.

The Phase 1 pipeline shape established in v1 (lexer → reorderer →
parser → analyzer → interpreter, with the canonical renderer and
structured-result handling around them) is unchanged through v2a, v2b,
v2c, and v2d — every sequential extension since v1 adds rules to
existing modules without adding stages or moving the I/O boundary.
v3a adds a **Phase 2 layer** on top: a handler table populated during
Phase 1 + a listener generator that drives Phase 2 reactive execution
from an external event queue. Phase 2 reuses every Phase 1 stage
(re-analyzes, re-executes action statements) but adds initial
evaluation, event-loop drain, cascading, cycle detection, and
shutdown bookkeeping.

For module-level implementation details, read the source under
`src/liminate/`. For the authoritative behavior, read `docs/spec/`.

## The path of a line (Phase 1)

```
source line (or grouped when-block)
   │
   ▼
┌─────────────┐
│   lexer     │  tokens + leading-indent
└─────────────┘
   │
   ▼
┌─────────────┐
│  reorderer  │  canonical-order tokens
└─────────────┘
   │
   ▼
┌──────────────────────────────────────────┐       ┌────────────────────┐
│  parser (or parse_when_block for v3a)    │──────▶│ canonical renderer │  echoes "I understand this as: ..."
└──────────────────────────────────────────┘       └────────────────────┘
   │
   ▼
┌──────────────────┐
│ semantic analyzer│
└──────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────┐
│ interpreter — executes immediately, or for WhenNode          │
│ registers the handler into the HandlerTable for Phase 2      │
└──────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────┐
│  structured result  │  (one of nine Phase 1 outcomes)
└─────────────────────┘
   │
   ▼
┌────────────┐
│   CLI      │  prints the canonical preview, output, or error
└────────────┘
```

Each stage either passes work forward or short-circuits with a
structured result. No stage prints or reads — only the CLI does
that.

## Phase 2 — reactive listener (v3a)

After Phase 1 completes, the CLI checks two gates: (1) at least one
`when` handler registered, and (2) zero Phase 1 errors / unresolved
ambers. If both pass, the listener generator (`src/liminate/listener.py`)
takes over:

```
                  ┌────────────────────────────┐
                  │       HandlerTable          │  (registered during Phase 1)
                  └────────────────────────────┘
                                │
                                ▼
                  ┌────────────────────────────┐
                  │   LISTENING result          │  "watching: [...names...]"
                  └────────────────────────────┘
                                │
                                ▼
                  ┌────────────────────────────┐
                  │  initial evaluation         │  fire eligible handlers (registration order)
                  └────────────────────────────┘
                                │
                                ▼
                  ┌────────────────────────────┐
                  │ start adapters → event queue│
                  └────────────────────────────┘
                                │
                ┌───────────────┴─────────────────┐
                │       single-threaded loop      │
                │ ┌─────────────────────────────┐ │
                │ │ dequeue AdapterUpdate /     │ │
                │ │   AdapterDone / Failure     │ │
                │ │ change detection (deep eq.) │ │
                │ │ write symbol table          │ │
                │ │ re-eval dependent handlers  │ │
                │ │ fire false→true transitions │ │
                │ │   (action block analyzed +  │ │
                │ │    executed; HANDLER_FIRE   │ │
                │ │    per statement)           │ │
                │ │ cascade depth-first         │ │
                │ │ cycle detection             │ │
                │ └─────────────────────────────┘ │
                └─────────────────────────────────┘
                                │
                                ▼
                  ┌────────────────────────────┐
                  │   SHUTDOWN result           │  reason: finish | adapter_complete | no_adapters | external | error
                  └────────────────────────────┘
```

The whole listener is a Python generator yielding `LiminateResult`
objects in order: `LISTENING` → zero or more `HANDLER_FIRE` /
`ERROR_SEMANTIC` (action errors) / `ERROR_RUNTIME` (cycle / adapter
failure) → terminal `SHUTDOWN`. The CLI streams them to stdout the
same way it renders Phase 1 results, just with different status
handling.

## Stage by stage

### Lexer

Turns a single source line into a list of typed tokens. The lexer is
the most mechanical stage:

- Lowercases everything.
- Strips decorative punctuation (commas, periods, question marks,
  exclamation marks) from the edges of words.
- Splits on whitespace, keeping hyphenated names like
  `find-big-orders` together.
- Recognizes the colon `:` as its own token (used in composition
  definitions and `choose` branches).
- Combines `equal` followed by `to` into a single operator token
  `equal_to`.
- Accumulates a `"..."` run as a single `QUOTED_STRING` token (v2c
  §86). Quoted content preserves spaces and any punctuation; the
  vocabulary lookup is bypassed for quoted tokens (§89).
- Identifies blank lines (and lines that are only punctuation) as
  producing zero tokens, which the rest of the pipeline skips.
- Exposes a separate `leading_indent(line)` helper (v3a §110) that
  counts the leading spaces on a line and rejects tabs in the
  leading-whitespace run with a clear error. The CLI's file driver
  uses this to identify `when` action blocks.

Each token carries a category: verb, connective, operator, article,
delimiter, number, quoted-string, or unknown. "Unknown" simply means
"not in the reserved vocabulary" — that is where user-provided names
live; multi-word string values live in quoted-string.

### Reorderer

Liminate expects canonical word order (`verb the target ...`). The
reorderer accepts a narrow set of natural variations and rejects
everything else with a suggestion. In particular it accepts:

- Canonical order: `filter the orders where total is above 50`.
- Target before verb with an article: `the orders filter where total
  is above 50` → reordered to canonical.
- Target before verb without an article: `orders filter where total
  is above 50` → reordered to canonical.

Anything else (verb at the end, scrambled condition elements, etc.)
produces a parse error with a canonical-form suggestion. The wider
free-order acceptance is reserved for the future tile-composition
interface; the v1 text interpreter keeps the acceptance band narrow
on purpose.

If the input has no recognizable verb at all, the reorderer passes
the tokens through so the parser can try the named-composition
fallback.

### Parser

Builds an abstract syntax tree (AST). The parser is **slot-filling**:
each verb has a known signature (e.g. `filter` expects a target and a
condition), and the parser walks the tokens filling each slot in
canonical order. The twenty-one verbs (`remember`, `show`, `filter`,
`keep`, `count`, `gather`, `sum`, `each`, `choose`, `finish`,
`add`, `remove`, `weakens`, `require`, `forbid`, `permit`, `assign`,
`expect`, `sort`, `compare`, `transform`) each route to a verb-specific
sub-parser that
shares helpers — `keep` and `filter` share their target-plus-condition
shape, for instance.

Several words in the language change meaning depending on context.
The parser resolves all of them deterministically with parser state
plus one-token lookahead:

- `and` / `or` — list construction, compound condition, operation
  sequencing, record-field continuation, or multi-field display
  inside `each ... show` (five contexts).
- `is` — comparison introducer (followed by an operator) or equality
  operator (followed by a value).
- `not` — always modifies the operator that follows.
- `to` — range endpoint after `from <number>`, or part of `equal to`.
- `from` — range start in `gather`, result capture in `remember`
  (next token is a verb), simple reference (next token is a name),
  composition parameter declaration after `how to <name>`, or
  parameter passing after a composition call (v2d §96).
- `each` — iteration verb in verb position; pronoun for the current
  item inside a `where` clause.
- `of` — field-access connective in any value position (v2b §77).
- `if` / `otherwise` — branch introducers inside `choose` (v2d §99).
- `when` — top-level handler registration; rejected with a specific
  error in any nested position (v3a §108).
- `unless` — guard clause on a `when` line; rejected anywhere else
  (v3a §109).

If any condition (in `where`, `choose if`, `when`, or `unless`) mixes
both `and` and `or`, the parse still succeeds (standard precedence:
`and` binds tighter than `or`), but the parser flags an amber-
precedence outcome so the user can confirm the grouping before
execution. v3a §123 extended this rule to `when` and `unless`.

A second top-level parser entry point, `parse_when_block(header,
action_lines)`, handles v3a §110 indented action blocks. The CLI's
file driver buffers indented lines after a top-level `when` and
calls this entry. The parser enforces the indentation rules: same
depth throughout, deeper-than-block is a parse error, empty block is
a parse error, optional colon at end of the `when` line.

If parsing fails, the parser returns a parse error with a plain-
English message — never an "unexpected token at column N" style
error.

### Canonical renderer

The renderer is the inverse of the parser. It walks the AST and
produces a canonical English sentence representing exactly what the
interpreter is about to run.

This sentence is what the CLI prints right before each statement
executes (unless you pass `--quiet`, which suppresses the echo while
keeping data output):

```
I understand this as: filter the orders where total is above 50
```

The renderer preserves your descriptor verbatim, so the prose you
wrote reads back the same way:

```
I understand this as: remember a domain called mobius with docs as 91 and words as 381476
```

(The interpreter ignores `domain` for semantics — descriptors are
decorative — but the canonical-prose echo keeps your wording.)

The renderer also produces a parenthesized variant for amber-
precedence messages so the user sees the parser's grouping in plain
form.

The canonical rendering is more than cosmetic — it round-trips. A
canonical sentence, fed back into the parser, produces the same AST.
That property is exercised by the test suite for every example in the
spec.

### Semantic analyzer

The analyzer takes the AST and the current symbol table and checks
that the operation makes sense before any execution happens. Among
the things it verifies:

- The names referenced actually exist in the symbol table.
- The operation matches the target's type: `filter`, `count`, and
  `each` need a list; `sum` needs a list of numbers.
- For field operations on a list of records, every record in the list
  actually has the referenced field.
- A list under construction has only one kind of item — numbers,
  text, or records — never a mix.
- A `gather` range is ascending and contains at most 10,000 items.
- Named compositions are checked for grammar at definition time and
  for name resolution at call time. v2d adds parameter shape checks
  at the call site (parameter declared ⇔ argument provided).
- v2b adds a void-result check on value-position composition calls:
  a composition whose last operation is `show`/`filter`/`each`/
  `choose`/`finish` cannot be captured in `remember the X from
  <comp>`.

For Phase 2 `when` registration, the analyzer validates only the
condition and `unless` guard (v3a §108) — action-block statements are
parsed at registration but their name resolution is deferred to
firing time, because actions may reference values created later by
other handlers or adapter updates.

v3a adds two listener-aware kwargs to `analyze()`:

- `in_action_block` — when True (set by the listener at firing time),
  `FinishNode` is legal (otherwise it's a semantic error); `remember`
  targeting a declared live-value name is a semantic error.
- `live_value_names` — the set of names declared as live by registered
  domain packs. `filter` targeting any of these names is a semantic
  error in *all* contexts (destructive mutation of adapter-owned
  values is forbidden).

Each failure becomes a semantic-error result with a clear message.
Nothing executes if the analyzer is unhappy.

### Interpreter

The interpreter runs the validated AST against a mutable symbol
table. Key behaviors:

- **`remember` mutates the symbol table.** A new entry is created, or
  an existing one is silently overwritten. The type can change.
- **`filter` modifies the target list in place.** The original list
  loses items that did not match. There is no output on success.
- **`keep` returns a fresh list.** Like `filter` but non-destructive
  — the source is untouched. `keep` auto-shows its matches by
  default, or its result can be captured via `remember ... from keep
  ...`. This is the reuse primitive: a `keep`-based composition is
  callable repeatedly with the same input.
- **`count`, `gather`, and `sum` auto-show.** `gather` also
  stores its result under the parsed name. `keep` also auto-shows.
- **`sum` is non-destructive.** It returns a total without changing
  the source list; an empty list sums to `0`.
- **`each` runs the action once per item.** Inside the action, names
  resolve first against the current item (as a field on a record)
  and then against the symbol table. The sub-action can be `show
  <field>` or `show <field> and <field>` for multi-field display.
- **`choose` evaluates branches in order.** The first branch whose
  condition is true fires; the optional terminal `otherwise` runs as
  a fallback. `choose` is side-effect-only — composition return-value
  capture rejects it.
- **Composition calls with parameters** deep-copy the argument's
  value into the parameter name for the duration of the body, then
  restore any shadowed global on return (v2d §96).
- **Copy semantics everywhere.** Data is copied when stored or
  retrieved by name. Two names never alias the same underlying
  collection.
- **Stepwise execution.** When several operations are joined by `and`
  (sequencing, not condition), each one commits independently. If a
  later one fails, earlier side effects remain and the error message
  names what was completed (with proper capitalization).

For v3a, the interpreter also maintains:

- **A handler table.** Phase 1 `WhenNode` statements register here
  rather than execute. Each entry records the registration index,
  the AST, the set of names referenced in the condition and guard
  (the "dependencies"), the last-seen compound eligibility, and a
  disabled flag for adapter-failure isolation.
- **A `_FinishRequested` exception.** `finish` raises it from
  whatever depth (top-level action statement, `choose` branch,
  composition body) so the listener catches it cleanly and
  transitions to shutdown. The exception carries no payload — the
  listener already knows which handler was firing.
- **ContextVars for the action-block context.** When the listener
  fires a handler, it sets `_in_action_block` and
  `_live_value_names_ctx`. The internal re-analyses inside
  `_exec_composition_call` and nested-SequenceNode dispatch read
  these to validate per-op semantics with the right context.

### Structured result

Every Phase 1 statement produces exactly one of nine outcomes:

| Outcome                | Meaning                                              |
|------------------------|------------------------------------------------------|
| `success`              | Parse, analysis, and execution all succeeded.        |
| `amber_precedence`     | A condition mixes `and` and `or`. Awaiting user confirmation. |
| `amber_ambiguity`      | The reorderer cannot uniquely resolve slot filling. Awaiting clarification. |
| `error_parse`          | The AST could not be built (including v3a indentation rule violations). |
| `error_semantic`       | The AST built, but execution would not make sense.   |
| `requirement_not_met`  | A `require` condition evaluated false at runtime — the data violates a rule (distinct from a program bug). |
| `prohibition_violated` | A `forbid` condition evaluated true at runtime — the data triggers a prohibition. |
| `permitted`            | A `permit` condition evaluated true at runtime — informational; execution continues. |
| `pack_verb_failure`    | A pack verb's verification check (`cite`/`verify`/`measure`) found a mismatch. Metadata carries the pack, verb, failure type, and slot values. |

Phase 2 listener mode adds four more (v3a §122):

| Outcome           | Meaning                                                       |
|-------------------|---------------------------------------------------------------|
| `listening`       | Phase 2 entry marker. Carries the set of watched names.       |
| `handler_fire`    | An action-block statement ran during firing. Wrapped with `trigger` metadata: source, handler index, names changed, new values. |
| `shutdown`        | Listener terminated. Carries `reason` metadata.               |
| `error_runtime`   | Cycle detected, adapter failure, or adapter type mismatch.    |

The result carries the canonical prose form, any output lines, an
explanation message for non-success outcomes, an `executed` flag,
and (for Phase 2 results) a metadata dict with the trigger envelope
or shutdown reason.

This is the full result vocabulary. There is no "warning" category,
no silent fallback, no probabilistic outcome. The interpreter is
deterministic: the prose either runs as written or it does not run
at all.

### CLI display

The CLI wrapper (`src/liminate/cli.py`) is the only module that calls
`input()` or `print()`. It receives the structured result and renders
it for the terminal:

- For success it prints the canonical preview line, then any output
  lines. The preview is suppressed under `--quiet`.
- For amber outcomes it prints the message and prompts for
  confirmation (or auto-confirms in `--test` mode). On confirmation
  the canonical preview is not re-emitted before execution.
- For errors it prints the message prefixed with `Error:`.
- For `listening` it prints `Listening for changes to: ...`.
- For `handler_fire` it prints output the same way it prints success
  output (the trigger metadata is available to embedders via the
  result dict; the CLI doesn't expose it in the terminal stream).
- For `shutdown` it prints the shutdown message (e.g. `Program
  stopped.`, `No event sources registered. Initial evaluation
  complete.`, `All event sources finished. Listener mode complete.`).

The CLI also applies two display refinements:

- **Auto-show truncation.** When `gather` or `keep` auto-shows a list
  longer than 20 items, the display is condensed to the first 10
  items, an ellipsis, and the last 10 items. The symbol table holds
  the full list; only the display is shortened. Explicit `show
  <list>` is never truncated — you asked for the whole list.
- **Blank-line preservation in `--quiet`.** Blank lines in the source
  file mirror to the output so paragraph breaks survive.

The file driver buffers indented action lines after a top-level
`when` line and hands the buffered block to `Session.run_when_block`.
Indentation rule violations (tabs in leading whitespace, deeper-than-
block depth, empty block, etc.) surface as Phase 1 ERROR_PARSE
results.

v3a adds the `--pack <path>` flag. The argument is the path to a JSON
file describing a `TestDomainPack`: a list of live-value declarations
plus a script of `[name, value]` updates (with the optional terminal
sentinel `"[done]"`). Multiple `--pack` flags accumulate. The CLI
constructs the corresponding `Session(domain_packs=...)` before
running the file.

Flags can appear in any argument position, and unknown `--flag`
typos error rather than silently falling through.

If you embed the interpreter in another program, you bypass the CLI
and inspect the structured result directly. The Phase 2 listener is
a Python generator (`liminate.listener.listen(...)`) yielding the
same `LiminateResult` objects the CLI streams. Every behavior the
CLI shows the user is available as plain data.

## Why this shape

Each stage exists because it solves one specific problem the
preceding stage cannot:

- A free-form text source needs **tokenization** before any structure
  can emerge.
- A bounded but human-friendly word order needs a **reorderer** to
  bridge typed prose to a canonical grammar.
- A grammar with many context-dependent words needs a **parser**
  with state and lookahead.
- A user-facing language needs a **canonical renderer** so the user
  can always see what the parser understood.
- A typed data model with field-based filtering needs a **semantic
  analyzer** to catch problems before execution.
- An interpreter that prints to a terminal in one deployment, runs in
  a tile interface in another, and is embedded in tests in a third
  needs to **return data**, not perform I/O.

And for v3a, two more:

- A reactive runtime that fires user code in response to external
  events needs a **handler table** registered during the sequential
  phase, plus a **listener generator** to drive Phase 2 from a
  single-threaded event queue. The generator yields structured
  results the same way the Phase 1 pipeline does — the consumer
  doesn't need to know which phase produced a result.
- A reactive runtime that mutates shared state from inside event
  handlers needs **edge-triggered evaluation with conservative cycle
  detection** so the cascade rules are predictable. Same-handler-
  twice in one chain is rejected; the loop doesn't run away.

Five Phase 1 stages, one Phase 2 layer, one boundary for I/O, thirteen
possible outcomes per statement (nine Phase 1 + four Phase 2).
Nothing more.

## Where to go next

- [`../language/quickstart.md`](../language/quickstart.md) — install
  and run the interpreter, including a Phase 2 listener example.
- [`../language/syntax.md`](../language/syntax.md) — the full
  syntax tour through v3a.
- [`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md) —
  what the interpreter includes and what is intentionally deferred.
- `src/liminate/` — the module-by-module implementation, including
  `listener.py` (Phase 2 generator) and `adapter.py` (DomainPack /
  Adapter / TestAdapter / LiveValueRegistry).
- [`../spec/`](../spec/) — the locked specification documents.

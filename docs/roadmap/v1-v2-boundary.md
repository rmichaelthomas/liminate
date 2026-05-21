# Build boundary

A guide to what Liminate currently is and what it intentionally is not. Every absence is a design decision, not a missing feature.

(This document was originally titled "v1 → v2 boundary" before v2b/v2c/v2d/v3a all shipped. The filename is kept for incoming links; the framing now covers the whole boundary, not just the v1/v2 line.)

## How to read this document

The Liminate interpreter is a **deliberately bounded artifact**: a deterministic two-phase text interpreter for sequential rules, data operations, reusable parameterized filters, conditional branching, and reactive handlers driven by external event sources. The sequential feature set (v1 → v2d) and the reactive feature set (v3a) together form a structurally complete programming language. Items in the "not yet built" sections below are not on a TODO list — each has a documented reason and either a deferred-to-spec plan or an explicit closed-door decision. Each is referenced in a specification document under `docs/spec/`.

If a feature is shipped, it has a locked specification, a working implementation, and passing tests. If it is not yet shipped, the interpreter does not pretend it exists: it produces a deterministic error.

## Build state at a glance (May 12, 2026)

| Layer | Status | Spec |
|---|---|---|
| **v1 interpreter** | Shipped. 48 locked test sentences pass end-to-end. | Inception checkpoint + v1a/v1b/v1c/v1d |
| **v2a additions** | Shipped. `keep` verb, `of` connective (in `show`), multi-field `each show`, descriptor preservation, composition-chaining error wording. | v2a §67–§72 |
| **v1 UX polish** | Shipped. `--quiet` flag, named-offender error wording, auto-show truncation (`gather`/`keep` only). | — (code-only patches) |
| **v2.1-patches** | Shipped. Duplicate-field rejection in `each show`, `of`-on-list suggestion, list-operations-only error wording. | Locked retroactively in v2b §78–§80 |
| **v2b additions** | Shipped. Composition return values (Path A: implicit return of the last op's value, error at call site for void-result), generalized `of` to all value positions. | v2b §76–§81 |
| **v2c additions** | Shipped. Quoting mechanism for multi-word string values, conditional rendering, quoted reserved words bypass vocabulary exclusion. | v2c §86–§92 |
| **v2d additions** | Shipped. Composition parameters with `from`, parameterized calls in value-capture position, `choose if`/`otherwise` conditional branching. | v2d §96–§105 |
| **v3a additions** | Shipped. Two-phase execution, `when`/`unless`/`finish`, indentation-based action blocks, single-threaded event queue, cascading triggers with conservative cycle detection, domain-pack adapter contract. | v3a §107–§126 |
| **Tile interface** | Not built — deferred. Branch C in the inception roadmap. | Inception §27 |
| **Proposal engine** | Not built — deferred. Branch E (Narratia integration). | Inception §27 |
| **Domain packs as product surfaces** | Not built — deferred. Healthcare/smart-home/game packs are product work; the language ships a test adapter only. | v3a §118/§126 |
| **Arithmetic operators** | Shipped. `by`/`plus`/`minus`/`multiplied by`/`divided by`, arithmetic expressions with PEMDAS precedence in value positions. | Infrastructure Era (PR #11) |
| **`sort` verb + `reverse`** | Shipped. In-place list reordering by a field, ascending or `in reverse`. | Infrastructure Era batch 2 (PR #12) |
| **`compare` verb** | Shipped. Structured comparison of two values into a `comparison` record (`status` + `divergences`). Promoted from reserved. | V2 promotion (PR #13) |
| **`transform` verb** | Shipped. Per-element list mutation via arithmetic expressions. The final V2-deferred word — `V2_RESERVED` is now empty. | V2 promotion (PR #14) |

## What is shipped

### Execution model

- **Two-phase execution.** Phase 1 runs every top-level sequential statement (`remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each`, `choose`, named composition calls) in source order. Phase 2 starts after Phase 1 completes with zero errors AND at least one `when` handler registered. (v3a §107)
- **Stepwise sequences.** When operations chain with `and` between complete verb phrases, each operation commits independently. A later failure does not roll back earlier side effects. (v1d §56)
- **Single-threaded event queue (Phase 2).** Adapters push `(name, value)` updates into a shared FIFO. The interpreter drains one update to completion (write → re-eval → fire-eligible → cascade) before the next dequeue. (v3a §119)
- **Edge-triggered evaluation (Phase 2).** Handlers fire on false→true transitions of their compound eligibility. Unchanged adapter updates are silently absorbed. Modifications inside an action block are coalesced by name and cascade depth-first. (v3a §113/§114)

### Vocabulary (54 reserved words)

- **19 verbs:** `remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each`, `choose`, `finish`, `add`, `remove`, `weakens`, `require`, `assign`, `expect`, `sort`, `compare`, `transform`.
- **20 connectives:** `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`, `of`, `if`, `otherwise`, `when`, `unless`, `includes`, `within`, `over`, `then`, `by`, `because`.
- **8 single-word operators:** `is`, `above`, `below`, `not`, `plus`, `minus`, `reverse`, `inherited`. Plus `equal`/`multiplied`/`divided` as multi-word components (combine with `to`/`by` per inception §22).
- **3 articles:** `the`, `a`, `an`.
- **1 declaration:** `about`.
- **1 delimiter:** `:`.
- **0 v2-deferred:** `V2_RESERVED` is now empty — `transform` and `compare` have been promoted to active verbs.

The Meta-Structural Era added three self-describing words as inert metadata (visible to rendering and `inspect`, never executed): `about` (program topic declaration, first line), `because` (statement-terminal quoted rationale on any verb statement), and `inherited` (statement-initial provenance modifier marking a statement as carried forward from a prior context, with optional `from <agent>` attribution).

### Data types and values

- **Numbers** — non-negative integers and decimals (`30`, `3.14`).
- **Single-word strings** — bare words that are neither numbers nor reserved words (`active`, `portland`). Case-folded to lowercase.
- **Multi-word / quoted strings** — `"in progress"`, `"high priority"`. Values only (names use hyphens). Quoting bypasses the reserved-word vocabulary lookup, so `with label as "filter"` stores the literal string "filter". The renderer drops quotes around safe single-word values when echoing canonical prose. (v2c §86–§92)
- **Homogeneous lists** — all numbers, all strings, or all records.
- **Records** — named-field bundles built with `as`.
- **Named compositions** — reusable verb phrases stored under a user-defined name. Optionally take one parameter declared with `from <param>` in the definition and passed with `from <name>` at the call site (v2d §96).

### Operations

- **In-place `filter`** — modifies the target list directly.
- **Non-destructive `keep`** (v2a §67) — returns a fresh list of matches; source unchanged. Auto-shows by default; captures via `remember ... from keep ...`. Enables reusable filter compositions.
- **Non-destructive `combine`** — returns the sum without changing the source.
- **Generalized `of`** (v2b §77) — `<field> of <record>` works in any value position: after `show`, in `where`/`choose if`/`when`/`unless` conditions on either side, in `with`/`from` value position. Single-level only; chained `of` (`a of b of c`) stays rejected until nested records exist.
- **Multi-field `each show`** (v2a §69) — `each the docs show A and B` emits `A: ..., B: ...` per record. Duplicate field names are a semantic error.
- **`choose` conditional branching** (v2d §99) — `choose if <cond>: <action> [otherwise [if <cond>:] <action>]*`. First matching branch fires; terminal `otherwise` is a fallback. Side-effect-only.
- **`when` handler registration** (v3a §108) — `when <cond> [unless <guard>]` at indent 0, with an indented action block. Action block is parsed at registration; name resolution inside it is deferred to firing time.
- **`finish` immediate-and-total shutdown** (v3a §112) — inside an action block (directly, inside a `choose` branch, or inside a composition called from one), `finish` terminates the listener. Yields only the SHUTDOWN result.
- **Composition return values** (v2b §76) — `remember the X from <comp>` captures the value of the composition's last operation. Side-effect-only last ops (`show`/`filter`/`each`/`choose`/`finish`) are rejected at the call site.
- **Composition parameters** (v2d §96) — one named parameter, names-only, deep-copy semantics, local binding with global shadow/restore. Parameter-mismatch errors at the call site.
- **Auto-show** — `count`, `combine`, `gather`, and `keep` (standalone) display their results without an explicit `show`.
- **Copy semantics** — every data operation copies values. Two names never alias the same underlying collection.
- **Iterator context for `each`** — during iteration, names resolve first as a field on the current record, then against the symbol table.

### Reactive / event-driven (v3a)

- **Indented action blocks** (v3a §110) — minimum one space of indentation, tabs rejected, same depth throughout, deeper-than-block is a parse error, empty blocks are a parse error, blank lines inside are skipped.
- **`unless` guard** (v3a §109) — guard clause on `when`. Compound eligibility is `when-true AND NOT unless-true`. Each condition is parsed and amber-checked independently.
- **Edge-triggered firing** — false→true transitions only. Already-true conditions don't re-fire on every change; `keep` semantics for unchanged values absorb silently.
- **Cascading triggers** (v3a §114) — action-block writes are watched. Modified-name dependents re-evaluate depth-first; false→true transitions fire in registration order.
- **Conservative cycle detection** — same handler firing twice in one cascade chain is rejected with ERROR_RUNTIME; the handler stays active for future events.
- **Live-value lifecycle** (v3a §117) — declared by domain packs before Phase 1; transitions unset → active (on first adapter update or Phase 1 init) → inactive (on adapter failure). Conditions involving unset live values evaluate as false. `remember` on a live-value name inside an action block is rejected; `filter` on a live-value name is rejected in all contexts.
- **Domain-pack adapter contract** (v3a §116) — declarations + adapter (start/stop) + lifecycle. v3a ships a single concrete implementation, `TestAdapter`, for scripted, deterministic event-driven testing.
- **Domain pack registration** — external, via `--pack <path>` (JSON test pack) or `Session(domain_packs=...)`. No Liminate-level `use`/`load` verb.

### Display + validation

- **Deterministic outcomes only** — every Phase 1 statement produces exactly one of: success, amber-precedence, amber-ambiguity, parse error, semantic error. Phase 2 adds: listening, handler-fire, shutdown, runtime error. No warnings, no silent fallbacks. (v1c §50; v3a §122)
- **Canonical prose rendering** — the parser's interpretation of every successfully parsed statement is echoed back to the user before execution. Suppressed with `--quiet`. WhenNode renders as a multi-line block. (v1a §33; v3a §110)
- **Descriptor preservation** (v2a §71) — the user's descriptor (`a domain called X`) is preserved verbatim in canonical rendering rather than collapsed to `record`/`value`/`list`.
- **Named offenders in errors** — schema-mismatch errors call out the first record missing a field (with positional fallback when no source name is known). Zero-match vs. partial-match wording differs.
- **Auto-show truncation** — `gather`/`keep` auto-show output is truncated to first 10 + ellipsis + last 10 when the list exceeds 20 items. Explicit `show <list>` is never truncated.

### CLI

- **`--quiet`** — suppress the "I understand this as: ..." echo; mirror source blank lines so paragraph breaks survive.
- **`--test`** — auto-confirm amber prompts.
- **`--pack <path>`** — load a JSON test domain pack and register it with the Session. Multiple `--pack` flags accumulate.
- Flags work in any argument position; unknown `--flag` typos are rejected (not silently dropped).

## What is not yet built

Each item below is intentionally absent with a documented reason.

### Authoring surfaces (still deferred)

- **Tile-composition interface.** The visual surface that lets a first-time user arrange vocabulary tiles into sentences. Will share the AST with the text interpreter. (Inception §27, Branch C)
- **Proposal engine / authorize-don't-author authoring flow.** First touch on a working program, not a blank file. The text interpreter is the engine; the proposal engine is a separate component. (Inception §27, Branch E)
- **Symbolic syntax surface.** A future terse form (e.g. `orders.filter(total > 50)`) over the same AST.

### Vocabulary extensions (still deferred)

- **Real-world domain packs.** Healthcare, business, home automation, legal/compliance, narrative. Each pack adds 10–15 context-specific terms plus an adapter implementation. The language ships a `TestAdapter` only — real packs are downstream product work, not language work. (v3a §118/§126)
- **Domain pack activation via Liminate syntax.** A `use`/`load` verb that lets a program declare its adapter dependencies inline rather than via external `--pack` registration. Deferred deliberately at v3a §118.
- **`transform` and `compare`.** Shipped — both promoted from reserved slots to active verbs (PR #13, PR #14). `compare <left> to <right>` produces a structured `comparison` record; `transform` mutates list elements in place via arithmetic expressions. `V2_RESERVED` is now empty: every word designed at inception has been built. (v2d §103, v3a §124)

### Execution-model extensions (still deferred)

- **`choose` inside `each`.** Deferred at v2d §102; deliberately closed at v3a §126. The list-level filtering model handles the discriminative cases that motivated it.
- **Sophisticated cycle detection.** v3a §114's same-handler-twice guard is conservative — a state-based detector that distinguishes terminating ping-pongs from infinite loops is deferred until a real use case demands it.
- **Adapter timeout / preemption.** v3a §119's single-threaded queue assumes handlers complete quickly. A long-running handler blocks the queue; acceptable for v3a, revisitable later.
- **External data sources beyond domain-pack adapters.** No databases, APIs, CSV imports, or non-source file reads inside the language. Data comes from `remember`, `gather`, or an adapter.
- **Scope isolation beyond the iterator context and composition parameters.** The symbol table is global between top-level statements. Compositions share the caller's symbol table except for their explicitly-declared parameter (v2d §96).
- **`when` nested inside other constructs.** `when` is top-level only — rejected at parse time inside compositions, `each` bodies, and other `when` action blocks. Closed at v3a §108.

### Values and types

- **Negative numbers.** All numeric literals are zero or positive.
- **Mixed-type lists.** A list cannot contain both numbers and text.
- **Nested records.** Records are flat field→value maps. Chained `of` (`field-a of field-b of record`) is reserved until nested records exist.

### Operations (still deferred)

- **Per-record decision logic inside `each`.** `each ... keep where ...` is rejected with a list-level-suggestion error. v2b §78 closed the door on `each ... do <verb>` — if a future use case emerges that genuinely needs per-record reasoning beyond the where-clause, it returns as a fresh design item.
- **Multi-parameter compositions.** v2d §96 ships a single named parameter only. Two or more parameters would need a different binding shape and a clearer call-site syntax.
- **Descending ranges.** `gather the numbers from 10 to 1` is a semantic error.
- **Ranges over 10,000 items.** `gather` is capped.
- **Reference / alias semantics.** All data operations copy. Two names cannot share the same underlying list.

## Why the boundary moves the way it does

Each shipping round resolves specific gaps surfaced by dogfooding the previous one:

- **v1 → v2a:** the first dogfooding pass found that destructive `filter` made multi-pass analysis painful (D2), that there was no way to display multiple fields per record in `each` (D1), and no way to extract a single field of a single record (D4). v2a addressed all three with minimal vocabulary growth.
- **v2a → v2.1-patches:** the v2a dogfooding pass and the v1 UX polish round handled six small UX items without spec change.
- **v2a → v2b:** the second dogfooding pass found that `keep`-based compositions weren't usefully reusable because compositions didn't return values (D9), and that `of` couldn't appear in `where` clauses or other value positions (D11). v2b addressed both.
- **v2b → v2c:** D7 (multi-word strings) got its dedicated checkpoint. v2c §85–§92 locks the quoting mechanism — multi-word and reserved-word values use `"..."` in value positions only; names continue to use hyphens.
- **v2c → v2d:** the language had `keep`-based filters reusable on one list at definition time, but each new target list needed a fresh composition. v2d §96 adds a single named parameter (`from <param>` in definition + `from <name>` at call site) so one composition serves many lists. v2d also activates `choose if/otherwise` for the conditional-branching case dogfooding had repeatedly hit.
- **v2d → v3a:** Q13 (event-driven execution) was the largest deferred chapter. v3a closes Branch F — `when`/`unless`/`finish`, indented action blocks, a two-phase model, the adapter contract, and the listener generator. The sequential feature set was structurally complete after v2d; v3a makes the reactive feature set structurally complete too.

The line moves only where dogfooding produces a sharply specified gap. The vocabulary budget is the clarity budget: every word added must pass the word salad test (inception §20) and every addendum locks the smallest spec change consistent with the surfaced gap.

## Where to go next

- [`../language/quickstart.md`](../language/quickstart.md) — install and run.
- [`../language/syntax.md`](../language/syntax.md) — what you can write today, including v3a `when`/`unless`/`finish`.
- [`../architecture/pipeline.md`](../architecture/pipeline.md) — how the interpreter is structured (Phase 1 + Phase 2 layers).
- [`../spec/`](../spec/) — the locked specification documents.
- [`../liminate_gap_inventory_2026_05_12_v1_dogfooding.md`](../liminate_gap_inventory_2026_05_12_v1_dogfooding.md) and [`../liminate_gap_inventory_2026_05_12_v2a_dogfooding.md`](../liminate_gap_inventory_2026_05_12_v2a_dogfooding.md) — the dogfooding inventories that drove the v2a and v2b spec work.

# Liminate

The sentence is the program.

*Part of the Prosecode family — a set of tools for writing, verifying, and transferring structured reasoning.*

Liminate is a prose-as-syntax language whose syntax is plain English. A small, bounded vocabulary of 58 reserved words combines into sentences that a real interpreter lexes, parses, type-checks, and runs. Not a prompt. Not a code generator. The prose IS the program.

## What it does

You write what you want in readable English, one statement per line, and the interpreter executes it directly. If the prose doesn't say it, it doesn't happen — no silent inference, no fuzzy parsing. If you write programs you'd rather other people could read, this is for you.

## Example

```
gather the numbers from 1 to 10
filter the numbers where each is above 5
combine the numbers
```

Run it:

```bash
liminate demo.limn
```

You get back `1, 2, 3, 4, 5, 6, 7, 8, 9, 10` and then `40` — the sum of what's left after filtering. The interpreter also echoes each statement in canonical form so you can see exactly how it was understood before it ran.

## Built by Liminate

Liminate is a prose-as-syntax language where plain English sentences execute directly. These five repos form a system for writing, verifying, and transferring structured reasoning.

| | Repo | What it does |
|---|---|---|
| **← this repo** | [**liminate**](https://github.com/rmichaelthomas/liminate) | **The language and interpreter. Bounded vocabulary, deterministic execution, domain packs.** |
| | [liminate-session-contracts](https://github.com/rmichaelthomas/liminate-session-contracts) | Tracks verified sources, inferred claims, locked decisions, and user corrections as executable `.limn` contracts. |
| | [prosecode-prompt-compiler](https://github.com/rmichaelthomas/prosecode-prompt-compiler) | Compiles user prompts into structured intent before the agent responds. Seven verbs, twenty-four slots. |
| | [prosecode-context-pager](https://github.com/rmichaelthomas/prosecode-context-pager) | Scores conversation history against current intent. Decides what to keep, summarize, or drop. |
| | [prosecode-handoff-packet](https://github.com/rmichaelthomas/prosecode-handoff-packet) | Packages a working session for another agent to continue — preserving what was verified and what wasn't. |

→ [liminate.dev](https://liminate.dev)

The two-tier naming is intentional: `liminate-*` is the substrate (the language and its native formats), `prosecode-*` is the processing layer (tools that operate on context).

## Install

Requires Python 3.10+.

```bash
pipx install liminate
# or:
pip install liminate

liminate --version
liminate demo.limn
```

The interpreter runs entirely on your machine. No network calls, no telemetry, no server dependency.

Standalone binaries for macOS, Linux, and Windows are on the [Releases page](https://github.com/rmichaelthomas/liminate/releases) — no Python needed.

For contributors:

```bash
git clone https://github.com/rmichaelthomas/liminate.git
cd liminate
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pytest tests/
```

## How it works

The current build is **v0.14.0**: 21 verbs, 22 connectives, 8 operators, 1 declaration, 58 base reserved words, **1456 tests passing**.

### The pipeline

Five processing stages — lexer, reorderer, parser, semantic analyzer, interpreter — with canonical rendering and structured-result handling. No `print` calls outside the CLI wrapper; every module returns a structured `LiminateResult`.

Two phases of execution:

- **Phase 1 — sequential.** Each statement runs in order. Stepwise commit: if a later op fails, earlier side effects remain and the error names what was completed.
- **Phase 2 — reactive listener.** `when`/`unless` register handlers driven by an external event source (a domain pack adapter). Edge-triggered, depth-first cascading, conservative same-handler-twice cycle detection. `finish` exits immediately and totally.

### The vocabulary (58 words)

**Verbs (21):** `remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each`, `choose`, `finish`, `add`, `remove`, `weakens`, `require`, `forbid`, `permit`, `assign`, `expect`, `sort`, `compare`, `transform`. The Deontic Era completes the obligation/prohibition/permission triangle: `require` halts when its condition is false, `forbid` halts when its condition is true (`PROHIBITION_VIOLATED`), and `permit` emits an informational line when its condition is true but never halts.

**Connectives (22):** `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`, `of`, `if`, `otherwise`, `when`, `unless`, `includes`, `within`, `over`, `then`, `by`, `because`, `starting`, `until`. `because` attaches a quoted rationale to any verb statement as inert metadata — visible in canonical rendering, `inspect`, and Receipts, but never executed. Statement-terminal and per-statement: `require amount is above 50000 because "SOX compliance"`. The last two, `starting` and `until`, are statement-initial temporal modifiers that attach quoted ISO 8601 dates as inert metadata — an effective date and a sunset clause: `starting "2025-07-01" until "2025-12-31" require amount is above 50000`. Temporal evaluation is a product-layer concern, not interpreter runtime.

**Operators (8):** `is`, `above`, `below`, `not`, `plus`, `minus`, `reverse`, `inherited`. Multi-word: `equal to`, `multiplied by`, `divided by`. The last, `inherited`, is a statement-initial modifier marking a verb statement as carried forward from a prior context (session, agent, contract) — inert provenance metadata, overridable, never executed. It reuses the `from` connective for statement-final agent attribution: `inherited require amount is above 50000 because "SOX compliance" from agent-compliance`.

**Articles (3):** `the`, `a`, `an` — decorative; the parser ignores them.

**Declarations (1):** `about` — declares the program's topic as inert metadata. Single, first-line-only; visible to tooling (`inspect`, the build manifest) but never stored or executed. `about "expense authorization"` or `about expense-authorization`.

**Delimiter (1):** `:` — separates a composition name from its body, and a `choose` branch's condition from its action.

`"..."` brackets a multi-word string value or one that would collide with a reserved word. Quotes are value-position only; names use hyphens. Quoted content is preserved verbatim, case included.

Arithmetic expressions use PEMDAS precedence (multiply/divide before add/subtract, left-to-right within the same tier) and work in any value position.

### Domain packs

A pack is a small JSON file that adds nouns and verbs while it's loaded. The base 58 words are permanent; pack-contributed words are reserved only when the pack is active.

A pack verb declares a slot signature, a type constraint, and one of six execution dispatches:

| Execution | What it does |
|---|---|
| `set_value` | Write a value into a named live-value or record field. |
| `substring_check` | Case-sensitive containment check against a target string; error if missing. |
| `append_to_list` | Deep-copy append to a list with the v1-add safety checks. |
| `set_field` | Set or create a field on a record (updates the schema). |
| `compare_values` | Equality or structural comparison; emit status + diff to two targets. |
| `numeric_extract_compare` | Extract a number from text, compare within tolerance, emit match/delta. |

Bundled packs: `timer`, `stdin`, `file-watcher`, `research`, plus a UI reference pack (`screen`, `button`, etc. + `navigate to <screen>`).

### Build a standalone binary

```bash
liminate build demo.limn --output demo
./demo
./demo --inspect          # source, canonical rendering, packs, vocabulary in use
```

Bundle packs the same way you'd register them at runtime — file path or inline JSON, repeatable.

### Run examples

```bash
liminate examples/program1_basics.limn
liminate --quiet examples/dogfood_v2a_14_realistic.limn

# Event-driven listener
liminate --pack examples/dogfood_v3a_pack.json --test --quiet \
    examples/dogfood_v3a_event_driven.limn

# UI pack
liminate --pack examples/pack_ui.json --quiet \
    examples/dogfood_navigate_test.limn
```

### Project layout

```
liminate/
├── src/liminate/        Pipeline (lexer, reorderer, parser, renderer,
│                        analyzer, interpreter, listener, adapter, run, packs/)
├── tests/               1456 tests
├── examples/            Runnable .limn programs + reference packs
├── docs/spec/           Locked specification documents
└── docs/                Quickstart, syntax tour, pipeline walkthrough
```

### Test discipline

The locked test sentences are simultaneously test cases and grammar artifacts — the sentences ARE the discovered grammar. Design questions surface while writing them, get resolved in the specification, and only then does Python get written.

### Design principles

- **The prose IS the program.** No inference, no guessing. If the prose doesn't say it, it doesn't happen.
- **The vocabulary is the boundary.** 58 base reserved words. Expressiveness scales through composition and domain packs, not through adding keywords.
- **The reorderer does not guess.** Ambiguous arrangements produce an amber clarification prompt rather than a silent pick.
- **Authorize, don't author.** The on-ramp is modification of a working program, not authorship from a blank file.
- **The AST is the source of truth.** The parser reconstructs a canonical English sentence so you see what was understood before it runs.

## Security and data flow

See [TRUST-BOUNDARY.md](https://github.com/rmichaelthomas/liminate-session-contracts/blob/main/docs/TRUST-BOUNDARY.md) for a complete description of what data moves where across the three usage modes: local-only, Receipts save, and fragment-encoded inspection.

## License

Apache 2.0. See [LICENSE](LICENSE).

---

*A language is a tool for naming. The question was never whether non-programmers could think computationally — the question was why we kept handing them someone else's language to do it in.*

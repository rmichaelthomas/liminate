# Liminate

The sentence is the program.

Liminate is a programming language whose syntax is plain English. A small, bounded vocabulary of 40 reserved words combines into sentences that a real interpreter lexes, parses, type-checks, and runs. Not a prompt. Not a code generator. The prose IS the program.

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

## Part of the Liminate family

Liminate is a prose-as-syntax programming language where plain English sentences execute directly. These five repos form a system for writing, verifying, and transferring structured reasoning.

| | Repo | What it does |
|---|---|---|
| **← this repo** | [**liminate**](https://github.com/rmichaelthomas/liminate) | **The language and interpreter. Bounded vocabulary, deterministic execution, domain packs.** |
| | [liminate-session-contracts](https://github.com/rmichaelthomas/liminate-session-contracts) | Tracks verified sources, inferred claims, locked decisions, and user corrections as executable `.limn` contracts. |
| | [prosecode-prompt-compiler](https://github.com/rmichaelthomas/prosecode-prompt-compiler) | Compiles user prompts into structured intent before the agent responds. Seven verbs, twenty-four slots. |
| | [prosecode-context-pager](https://github.com/rmichaelthomas/prosecode-context-pager) | Scores conversation history against current intent. Decides what to keep, summarize, or drop. |
| | [prosecode-handoff-packet](https://github.com/rmichaelthomas/prosecode-handoff-packet) | Packages a working session for another agent to continue — preserving what was verified and what wasn't. |

→ [onesurface.org/liminate](https://onesurface.org/liminate)

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

The current build is **v0.2.0**: 13 verbs, 17 connectives, 40 base reserved words, **888 tests passing** across 127 locked test sentences.

### The pipeline

Five processing stages — lexer, reorderer, parser, semantic analyzer, interpreter — with canonical rendering and structured-result handling. No `print` calls outside the CLI wrapper; every module returns a structured `LiminateResult`.

Two phases of execution:

- **Phase 1 — sequential.** Each statement runs in order. Stepwise commit: if a later op fails, earlier side effects remain and the error names what was completed.
- **Phase 2 — reactive listener.** `when`/`unless` register handlers driven by an external event source (a domain pack adapter). Edge-triggered, depth-first cascading, conservative same-handler-twice cycle detection. `finish` exits immediately and totally.

### The vocabulary (40 words)

**Verbs (13):** `remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each`, `choose`, `finish`, `add`, `remove`, `weakens`.

**Connectives (17):** `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`, `of`, `if`, `otherwise`, `when`, `unless`, `includes`, `within`, `over`.

**Operators (5):** `is`, `above`, `below`, `equal to`, `not`.

**Articles (3):** `the`, `a`, `an` — decorative; the parser ignores them.

**Delimiter (1):** `:` — separates a composition name from its body, and a `choose` branch's condition from its action.

**Reserved but no grammar yet (2):** `transform`, `compare` — slots protected so user names won't collide.

`"..."` brackets a multi-word string value or one that would collide with a reserved word. Quotes are value-position only; names use hyphens. Quoted content is preserved verbatim, case included.

### Domain packs

A pack is a small JSON file that adds nouns and verbs while it's loaded. The base 40 words are permanent; pack-contributed words are reserved only when the pack is active.

A pack verb declares a slot signature, a type constraint, and one of five execution dispatches:

| Execution | What it does |
|---|---|
| `set_value` | Write a value into a named live-value or record field. |
| `substring_check` | Case-sensitive containment check against a target string; error if missing. |
| `append_to_list` | Deep-copy append to a list with the v1-add safety checks. |
| `set_field` | Set or create a field on a record (updates the schema). |
| `compare_values` | Equality or structural comparison; emit status + diff to two targets. |

Bundled packs: `timer`, `stdin`, `file-watcher`, plus a UI reference pack (`screen`, `button`, etc. + `navigate to <screen>`).

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
│                        analyzer, interpreter, listener, adapter, packs/)
├── tests/               888 tests across the 127 locked sentences
├── examples/            Runnable .limn programs + reference packs
├── docs/spec/           Locked specification documents
└── docs/                Quickstart, syntax tour, pipeline walkthrough
```

### Test discipline

The locked test sentences are simultaneously test cases and grammar artifacts — the sentences ARE the discovered grammar. Design questions surface while writing them, get resolved in the specification, and only then does Python get written.

### Design principles

- **The prose IS the program.** No inference, no guessing. If the prose doesn't say it, it doesn't happen.
- **The vocabulary is the boundary.** 40 base reserved words. Expressiveness scales through composition and domain packs, not through adding keywords.
- **The reorderer does not guess.** Ambiguous arrangements produce an amber clarification prompt rather than a silent pick.
- **Authorize, don't author.** The on-ramp is modification of a working program, not authorship from a blank file.
- **The AST is the source of truth.** The parser reconstructs a canonical English sentence so you see what was understood before it runs.

## License

Apache 2.0. See [LICENSE](LICENSE).

---

*A programming language is a tool for naming. The question was never whether non-programmers could think computationally — the question was why we kept handing them someone else's language to do it in.*

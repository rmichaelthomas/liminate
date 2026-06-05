# AGENTS.md — Liminate Programming Language

## Project Overview

Liminate is a prose-as-syntax programming language. The interpreter is a Python pipeline: lexer → reorderer → parser + renderer → analyzer → interpreter, with a Phase 2 event-driven listener layered on top.

Current vocabulary: 21 verbs, 22 connectives, 8 operators, 1 declaration, 58 reserved words. Domain packs may declare additional verbs and nouns via the pack-verb contract.

## Critical Rules

1. **No invented behavior.** If the language doesn't define what happens in a situation, the interpreter produces an error. No implicit type coercion, no helpful guessing, no "smart" defaults. The interpreter is deterministic. The prose IS the program.

2. **No direct I/O in core modules.** Only `cli.py` may call `input()` or `print()`. All other modules return structured `LiminateResult` objects.

3. **Test after every change.** Run `pytest tests/` before claiming a change works.

## Commands

```bash
# Print the installed version
liminate --version

# Run all tests
pytest tests/ -v

# Run a single module's tests
pytest tests/test_lexer.py -v
pytest tests/test_listener.py -v

# Run the interpreter on a file (Phase 1 sequential)
liminate examples/program1_basics.limn

# Run a file with the canonical-echo suppressed
liminate examples/program1_basics.limn --quiet

# Test mode (auto-confirms amber outcomes)
liminate examples/program2_orders.limn --test

# Phase 2 event-driven mode with a scripted test pack
liminate examples/dogfood_v3a_event_driven.limn \
    --pack examples/dogfood_v3a_pack.json --test --quiet

# Phase 2 with the timer pack (threaded source). `--pack` accepts a path
# OR an inline JSON string starting with `{`. The `type` field dispatches
# to the pack factory; `test` is the default.
liminate examples/dogfood_v3a_timer_pack.limn \
    --pack '{"type": "timer", "interval_ms": 200, "max_ticks": 5}' --quiet

# UI domain pack — pack-level `navigate to <screen>` verb + 10 component nouns
liminate --pack examples/pack_ui.json --quiet \
    examples/dogfood_navigate_test.limn

# Stdin reader pack — each piped line becomes a `line` live-value update
printf "hello\nworld\n" | liminate examples/dogfood_stdin_echo.limn \
    --pack '{"type": "stdin"}' --quiet

# File watcher pack — polls a directory and emits paired
# (changed-file, change-type) updates
liminate examples/dogfood_file_watcher.limn \
    --pack '{"type": "file-watcher", "path": "./inbox", "max_events": 1}' --quiet

# Interactive REPL (Phase 1 only)
liminate

# Build a standalone single-file binary for the current platform
./build/build_binary.sh

# Compile a Liminate program to a standalone executable
liminate build demo.limn --output demo
liminate build reactive.limn --pack monitor.json --output reactive

# Inspect a built binary
./demo --inspect
./demo --inspect --json
liminate inspect ./demo
liminate inspect ./demo --json
```

## Modules (src/liminate/)

- `lexer.py` — tokenizer with quote-state and leading-indent reporting.
- `vocabulary.py` — verb/connective/operator/article tables + the pack-verb dataclasses (`PackVerbSignature`, `PackVerbSlot`, and the discriminated execution-class union: `SetValueExecution`, `SubstringCheckExecution`, `AppendToListExecution`, `SetFieldExecution`, `CompareValuesExecution`, `NumericExtractCompareExecution`, `RangeCheckExecution`, `ConformanceCheckExecution`).
- `reorderer.py` — small permutation acceptor.
- `parser.py` — AST + `parse(tokens)` for single statements + `parse_when_block(header, action_lines)` for indented action blocks + `PackVerbNode` AST. Pack-verb dispatch runs after base verbs; slot parsing routes through `_parse_pack_slot_value` based on each slot's `value_type` (`"name"` or `"value"`).
- `renderer.py` — canonical prose, including multi-line `when` output.
- `analyzer.py` — semantic checks; `_check_pack_verb` `isinstance`-dispatches to per-execution validators against the entry's `descriptor`.
- `interpreter.py` — Phase 1 execution + `HandlerTable` + `_FinishRequested` exception + ContextVars for listener context. `_exec_pack_verb` is an eight-branch dispatch into the per-execution handlers. Shared helpers `_resolve_target` and `_resolve_source` implement the literal-vs-slot-derived target/source resolution model.
- `listener.py` — Phase 2 generator (`listen(...)`) — initial evaluation, event-queue drain, cascading, cycle detection, shutdown.
- `adapter.py` — `DomainPack`, `Adapter`, `TestAdapter`, `TestDomainPack`, `LiveValueRegistry`, optional `verbs()` / `vocabulary()` on `DomainPack`, and `parse_pack_verb_signature` (dispatches on execution `type` to one of the eight execution dataclasses; validates the load-time rules).
- `cli.py` — `Session` (owns symtab + handler table + registry + packs), `run_file` (with block buffering and Phase 2 entry), `--pack` flag.
- `packs/timer.py` — threaded periodic event source.
- `packs/stdin.py` — daemon-thread line reader.
- `packs/file_watcher.py` — directory polling source.
- `result.py` — `LiminateResult` with nine statuses + metadata.
- `build.py` — compiles a `.limn` file to a standalone PyInstaller binary; embeds source, pack JSON, and an inspection manifest.
- `inspect_cmd.py` — renders the four inspection sections (source / understood-as / packs / vocabulary-in-use) as text or JSON.

## Code Style

- Python 3.10+ (match statements, type unions with `|`).
- Dataclasses for structured data (Token, AST nodes, SymbolEntry, LiminateResult).
- Enums for fixed categories (TokenType, ResultStatus).
- Type hints on all function signatures.

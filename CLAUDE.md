# CLAUDE.md — Inscript Programming Language

## Project Overview

Inscript is a prose-as-syntax programming language designed by Rob Thomas (R. Michael Thomas). The v1 interpreter is being built in Python. You are the builder. Rob is the architect. All design decisions are locked in the specification documents.

## Critical Rules

1. **Read the spec before writing code.** All design decisions live in `docs/spec/`. When in doubt, read the relevant section — do not guess or pattern-match from the concept name.

2. **No invented behavior.** If the spec doesn't define what happens in a situation, the interpreter should produce an error. Do not add implicit intelligence, type coercion, helpful guessing, or "smart" defaults. The interpreter is deterministic. The prose IS the program. (See v1c §52.)

3. **No direct I/O in core modules.** Only `cli.py` may call `input()` or `print()`. All other modules return structured `InscriptResult` objects. (See v1d §64.)

4. **Test each phase before advancing.** Run `pytest tests/` after each phase. Do not build the parser before lexer tests pass.

5. **Every claim is load-bearing.** Do not state that a spec section says something without opening the file and verifying. This is the project's primary failure mode.

## Build Sequence

Follow `BUILD_PLAN.md` in the repo root. Seven phases, each with a gate:

1. Foundation (vocabulary.py, result.py)
2. Lexer (lexer.py)
3. Reorderer (reorderer.py)
4. Parser + Renderer (parser.py, renderer.py)
5. Semantic Analyzer (analyzer.py)
6. Interpreter (interpreter.py)
7. Integration (cli.py, test_integration.py)

## Specification Documents

Located in `docs/spec/`:

- `inscript_inception_checkpoint_v1.md` — Language design (vocabulary, pipeline, verb signatures, parser rules, interpreter behaviors)
- `inscript_addendum_v1a_pre_build.md` — Reserved words, amber light, canonical rendering
- `inscript_addendum_v1b_design_resolutions.md` — Eight design resolutions, complete disambiguation ruleset (§44)
- `inscript_addendum_v1c_implementation_hardening.md` — Value-position enforcement, iterator context, output taxonomy, parser lookahead, deterministic interpretation
- `inscript_addendum_v1d_build_boundary.md` — Final build locks: reorderer scope, stepwise execution, case normalization, duplicate handling, type constraints, range limits, structured results, build boundary

- `inscript_v1_thirty_sentences.md` — Test specification (sentences 1–30 + design questions). Additional sentences 31–34 in v1c §53, sentences 35–48 in v1d §65.

## Commands

```bash
# Run all tests
pytest tests/ -v

# Run a single phase's tests
pytest tests/test_lexer.py -v

# Run the interpreter on a file
python -m inscript examples/program1_basics.insc

# Interactive REPL
python -m inscript
```

## Code Style

- Python 3.10+ (for match statements, type unions with `|`)
- Use dataclasses for structured data (Token, AST nodes, SymbolEntry, InscriptResult)
- Use enums for fixed categories (TokenType, ResultStatus)
- Type hints on all function signatures
- Docstrings referencing spec section numbers for non-obvious decisions

# CLAUDE.md — Inscript Programming Language

## Project Overview

Inscript is a prose-as-syntax programming language designed by Rob Thomas (R. Michael Thomas). You are the builder. Rob is the architect. All design decisions are locked in the specification documents.

**Current state (May 12, 2026):** v1 interpreter + v2a (`keep` verb, `of` connective, multi-field `each show`, descriptor preservation) + UX polish (`--quiet` flag, named-offender error wording, auto-show truncation) + v2.1-patches (duplicate-field rejection, `of`-on-list suggestion, list-operations-only error) + v2b (composition return values, generalized `of`) + v2c (quoting mechanism for multi-word strings). The pipeline architecture from §8–§9 is unchanged through all extensions.

## Critical Rules

1. **Read the spec before writing code.** All design decisions live in `docs/spec/`. When in doubt, read the relevant section — do not guess or pattern-match from the concept name.

2. **No invented behavior.** If the spec doesn't define what happens in a situation, the interpreter should produce an error. Do not add implicit intelligence, type coercion, helpful guessing, or "smart" defaults. The interpreter is deterministic. The prose IS the program. (See v1c §52.)

3. **No direct I/O in core modules.** Only `cli.py` may call `input()` or `print()`. All other modules return structured `InscriptResult` objects. (See v1d §64.)

4. **Test each phase before advancing.** Run `pytest tests/` after each phase. Do not build the parser before lexer tests pass.

5. **Every claim is load-bearing.** Do not state that a spec section says something without opening the file and verifying. This is the project's primary failure mode.

## Build Sequence

The original v1 build followed the seven-phase plan in `BUILD_PLAN.md` (foundation → lexer → reorderer → parser+renderer → analyzer → interpreter → integration). Each phase had a gate. v1 shipped through all seven; subsequent addenda (v2a, v2.1-patches) extend the existing modules without adding phases. The `BUILD_PLAN.md` plan is preserved as historical record — read it for the original phase shape; read the most recent spec addenda for what the language currently does.

## Specification Documents

Located in `docs/spec/`. Read the relevant section before writing code that touches it.

**v1 build specification (locked, May 11, 2026):**

- `inscript_inception_checkpoint_v1.md` — Language design (vocabulary, pipeline, verb signatures, parser rules, interpreter behaviors)
- `inscript_addendum_v1a_pre_build.md` — Reserved words, amber light, canonical rendering
- `inscript_addendum_v1b_design_resolutions.md` — Eight design resolutions, complete disambiguation ruleset (§44)
- `inscript_addendum_v1c_implementation_hardening.md` — Value-position enforcement, iterator context, output taxonomy, parser lookahead, deterministic interpretation
- `inscript_addendum_v1d_build_boundary.md` — Final build locks: reorderer scope, stepwise execution, case normalization, duplicate handling, type constraints, range limits, structured results, build boundary

**v2 extensions (May 12, 2026):**

- `inscript_addendum_v2a_dogfooding_resolutions.md` — **LOCKED + IMPLEMENTED.** §67 `keep` verb (non-destructive filter), §68 `of` connective (`show <field> of <record>`, single-level), §69 fifth `and` context rule (multi-field `each show`), §70 composition-chaining error message, §71 descriptor preservation, §72 D7 (multi-word strings) deferral. Vocabulary: 8 verbs, 10 connectives, 31 reserved words.
- `inscript_addendum_v2b_composition_returns.md` — §76 composition return values (Path A: implicit return of last op; error at call site for void-result), §77 generalize `of` to any value position (single-level only), §78 list/iteration model clarification, §79–§81 UX items (U7/U8/U9). No vocabulary changes. Test sentences 60–68.
- `inscript_addendum_v2c_multi_word_strings.md` — D7 resolution: quoting mechanism for multi-word string values. §86 lexer quote-state, §87 `QUOTED_STRING` in value positions only (rejected in name/field positions with hyphenation guidance), §88 literal display via `show "..."`, §89 quoted reserved words bypass vocabulary exclusion, §90 conditional rendering (quote only multi-word or reserved-word values), §91 case normalization inside quotes, §92 empty quotes rejected. No new vocabulary. Test sentences 69–80.
- `inscript_checkpoint_v2c_multi_word_strings.md` — D7 analysis (context for the v2c addendum: three approaches evaluated; not a locked spec).

**Test specification:**

- `inscript_v1_thirty_sentences.md` — Test specification (sentences 1–30 + design questions). Additional sentences 31–34 in v1c §53, 35–48 in v1d §65, 49–59 in v2a §74, 60–68 in v2b §83, 69–80 in v2c §94.

**Reading order for a fresh session:** inception checkpoint → v1a/v1b/v1c/v1d in order → v2a → v2b → v2c. Each addendum locks decisions on top of all prior; nothing is retracted.

## Commands

```bash
# Run all tests (418 passing as of v2a + UX polish + v2.1-patches)
pytest tests/ -v

# Run a single module's tests
pytest tests/test_lexer.py -v

# Run the interpreter on a file
python -m inscript examples/program1_basics.insc

# Run a file with the canonical-echo suppressed (clean output)
python -m inscript examples/dogfood_1_corpus_summary.insc --quiet

# Test mode (auto-confirms amber outcomes; flags accepted in any position)
python -m inscript examples/program2_orders.insc --test
python -m inscript --test --quiet examples/dogfood_v2a_14_realistic.insc

# Interactive REPL
python -m inscript
```

## Code Style

- Python 3.10+ (for match statements, type unions with `|`)
- Use dataclasses for structured data (Token, AST nodes, SymbolEntry, InscriptResult)
- Use enums for fixed categories (TokenType, ResultStatus)
- Type hints on all function signatures
- Docstrings referencing spec section numbers for non-obvious decisions

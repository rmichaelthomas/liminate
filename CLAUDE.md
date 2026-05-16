# CLAUDE.md — Liminate Programming Language

## Project Overview

Liminate is a prose-as-syntax programming language designed by Rob Thomas (R. Michael Thomas). You are the builder. Rob is the architect. All design decisions are locked in the specification documents.

**Current state (May 13, 2026):** v1 interpreter + v2a (`keep` verb, `of` connective, multi-field `each show`, descriptor preservation) + UX polish (`--quiet` flag, named-offender error wording, auto-show truncation) + v2.1-patches (duplicate-field rejection, `of`-on-list suggestion, list-operations-only error) + v2b (composition return values, generalized `of`) + v2c (quoting mechanism for multi-word strings) + v2d (composition parameters with `from`, `choose` verb with `if`/`otherwise`) + v3a (event-driven listener mode: `when`/`unless` connectives, `finish` verb, two-phase execution, indentation-based action blocks, adapter contract, cascading triggers, conservative cycle detection) + v3b (quoted-string case preservation: lexer no longer folds case inside quotes; renderer adds case-bearing as a third conditional-quoting trigger) + **v4a (general-purpose pack verb contract: packs declare verbs with slot signatures, type constraints, and execution dispatch in JSON; UI domain pack with 10 component nouns and `navigate to <screen-name>`)**. The Phase 1 pipeline architecture from §8–§9 is unchanged through all extensions; Phase 2 adds a single-threaded event-queue runtime layered on top; v4a extends the parser/analyzer/interpreter dispatch tables without changing the base vocabulary. A separate TypeScript port of the validation pipeline (lexer + reorderer + parser + analyzer + renderer; no interpreter) lives in `mobius/packages/liminate-lang/` and validates against this implementation via the 127-sentence sync contract.

## Critical Rules

1. **Read the spec before writing code.** All design decisions live in `docs/spec/`. When in doubt, read the relevant section — do not guess or pattern-match from the concept name.

2. **No invented behavior.** If the spec doesn't define what happens in a situation, the interpreter should produce an error. Do not add implicit intelligence, type coercion, helpful guessing, or "smart" defaults. The interpreter is deterministic. The prose IS the program. (See v1c §52.)

3. **No direct I/O in core modules.** Only `cli.py` may call `input()` or `print()`. All other modules return structured `LiminateResult` objects. (See v1d §64.)

4. **Test each phase before advancing.** Run `pytest tests/` after each phase. Do not build the parser before lexer tests pass.

5. **Every claim is load-bearing.** Do not state that a spec section says something without opening the file and verifying. This is the project's primary failure mode.

## Build Sequence

The original v1 build followed the seven-phase plan in `BUILD_PLAN.md` (foundation → lexer → reorderer → parser+renderer → analyzer → interpreter → integration). Each phase had a gate. v1 shipped through all seven; subsequent addenda (v2a, v2.1-patches) extend the existing modules without adding phases. The `BUILD_PLAN.md` plan is preserved as historical record — read it for the original phase shape; read the most recent spec addenda for what the language currently does.

## Specification Documents

Located in `docs/spec/`. Read the relevant section before writing code that touches it.

**v1 build specification (locked, May 11, 2026):**

- `liminate_inception_checkpoint_v1.md` — Language design (vocabulary, pipeline, verb signatures, parser rules, interpreter behaviors)
- `liminate_addendum_v1a_pre_build.md` — Reserved words, amber light, canonical rendering
- `liminate_addendum_v1b_design_resolutions.md` — Eight design resolutions, complete disambiguation ruleset (§44)
- `liminate_addendum_v1c_implementation_hardening.md` — Value-position enforcement, iterator context, output taxonomy, parser lookahead, deterministic interpretation
- `liminate_addendum_v1d_build_boundary.md` — Final build locks: reorderer scope, stepwise execution, case normalization, duplicate handling, type constraints, range limits, structured results, build boundary

**v2 extensions (May 12, 2026):**

- `liminate_addendum_v2a_dogfooding_resolutions.md` — **LOCKED + IMPLEMENTED.** §67 `keep` verb (non-destructive filter), §68 `of` connective (`show <field> of <record>`, single-level), §69 fifth `and` context rule (multi-field `each show`), §70 composition-chaining error message, §71 descriptor preservation, §72 D7 (multi-word strings) deferral. Vocabulary: 8 verbs, 10 connectives, 31 reserved words.
- `liminate_addendum_v2b_composition_returns.md` — §76 composition return values (Path A: implicit return of last op; error at call site for void-result), §77 generalize `of` to any value position (single-level only), §78 list/iteration model clarification, §79–§81 UX items (U7/U8/U9). No vocabulary changes. Test sentences 60–68.
- `liminate_addendum_v2c_multi_word_strings.md` — D7 resolution: quoting mechanism for multi-word string values. §86 lexer quote-state, §87 `QUOTED_STRING` in value positions only (rejected in name/field positions with hyphenation guidance), §88 literal display via `show "..."`, §89 quoted reserved words bypass vocabulary exclusion, §90 conditional rendering (quote only multi-word or reserved-word values), §91 case normalization inside quotes, §92 empty quotes rejected. No new vocabulary. Test sentences 69–80.
- `liminate_checkpoint_v2c_multi_word_strings.md` — D7 analysis (context for the v2c addendum: three approaches evaluated; not a locked spec).
- `liminate_addendum_v2d_parameters_and_branching.md` — **LOCKED + IMPLEMENTED.** Resolves Q9 (composition parameters) fully and promotes `choose` from deferred to active. §96 named parameter declared with `from <param>` in the definition and passed with `from <name>` at the call site (single parameter, local scope with global shadow/restore, deep-copy semantics, names-only); §97 parameter-mismatch errors at the call site; §98 parameterized calls in value-capture position via peek-ahead (`remember … from <comp> from <name>`); §99 `choose if <cond>: <action> [otherwise [if <cond>:] <action>]*` with `if` and `otherwise` as new connectives; §100 conditions reuse value-expression operands (both sides; `of` on the left supported); §101 multi-way branching via `otherwise if` (short-circuit) and multi-statement actions via `and` inside a branch; §102 `choose` is side-effect only (added to v2b §76 list; `choose` inside `each` deferred). §103 `transform` and `compare` continue deferral. Vocabulary: **9 verbs, 12 connectives, 33 reserved words**. Test sentences 81–95. v2a §70's composition-chaining error path is superseded — `<comp> from <name>` is now parameter passing.
- `liminate_addendum_v3a_event_driven_execution.md` — **LOCKED + IMPLEMENTED.** Resolves Q13 and closes Branch F. §107 two-phase execution (Phase 1 sequential = v2d-identical; Phase 2 reactive, gated on zero Phase 1 errors and a non-empty handler table). §108 `when` registers a reactive handler with choose-style condition resolution and registration-time name validation; the action block is parsed but not executed at registration. §109 `unless` guard splits compound eligibility into condition AND NOT guard. §110 indentation-based action blocks (min 1 space, tabs rejected, same-depth throughout, deeper-than-block is a parse error, empty blocks rejected). §111 action block scope: all v2d verbs + `finish` legal; `remember` on live-value names rejected inside action blocks; `filter` on live-value names rejected everywhere. §112 `finish` verb — immediate-and-total exit, propagated via _FinishRequested exception out of any nesting depth. §113 edge-triggered evaluation with deep value equality; unset live values = false; modifications coalesced by name. §114 depth-first cascading with conservative same-handler-twice cycle detection. §115 registration-order firing with complete-turn semantics. §116 adapter contract: declaration + adapter + start/stop lifecycle; multiple-adapter-per-name disallowed. §117 live-value lifecycle: unset → active → inactive. §118 domain pack registration via CLI `--pack <path>` (JSON) or `Session(domain_packs=...)` constructor — no Liminate-level `use`/`load` verb. §119 single-threaded event queue. §120 adapter failure isolation. §121 initial evaluation before adapter dispatch. §122 result interface: four new statuses (`listening`, `handler_fire`, `shutdown`, `error_runtime`) + trigger and shutdown metadata. §123 amber at registration for mixed and/or in when/unless. Vocabulary: **10 verbs, 14 connectives, 34 reserved words** (`finish` added; `when`/`unless` promoted from V2_RESERVED). Test sentences 96–113.
- **v3a external-review fixes (May 13, 2026):** Sentence 101 program corrected to produce a real cycle under §113 deep-equality; sentence 107 split into 107a/107b; Tier 1 (T1–T7) and Tier 2 (T8–T19) coverage tests added — see the POST-BUILD PATCHES section in the v3a addendum. No spec semantics changed; gaps were in test coverage and documentation only.

- **v3a UX fixes (May 13, 2026):** CLI display improvements U1/U2/U3 — HANDLER_FIRE results no longer print the Phase-1 "I understand this as: …" preview; each firing's first output line is prefixed with a compact trigger tag (`[initial]`, `[name → value]`, `[cascade: <names> changed]`); shutdown messages encode the reason (`Listener stopped: finish called.` / `… all event sources completed.` / `… no event sources registered.` / `… error (see above).` / `… interrupted.`); the LISTENING marker reports watching names in source-walk registration order (Handler gains a `dependency_order` tuple alongside the existing `dependencies` frozenset). Reactive patterns guide added at `docs/guide/reactive_patterns.md`.

- `liminate_addendum_v3b_quoted_string_case_preservation.md` — **LOCKED + IMPLEMENTED.** Patch-shaped addendum. §127 supersedes v2c §91 — quoted-string content is preserved verbatim, including case (`"In Progress"` stores `In Progress`, not `in progress`). The lexer's case-folding step is bypassed inside quoted-content accumulation; everything between quote marks is data. §128 extends v2c §90 with a third conditional-quoting trigger: the renderer emits quotes whenever the stored value differs from its lowercased form, preserving the round-trip property. §129 documents migration impact (programs with all-lowercase quoted content unaffected; mixed-case quoted content now stores verbatim; `where` equality on quoted values is case-sensitive). §130 vocabulary unchanged (still 10/14/34). §131 test sentences 114–117. §132 build boundary extends by two one-line code changes (`lexer.py` `_strip_and_lower`, `renderer.py` `_emit_string`).

- `liminate_addendum_v4a_pack_verbs_and_port.md` — **LOCKED + IMPLEMENTED (Python Phase 1; TypeScript Phase 2 in Möbius monorepo).** §134 UI domain pack vocabulary: 10 nouns (`screen`, `button`, `input`, `text`, `list-view`, `card`, `image`, `section`, `header`, `nav`). §135 `navigate` as pack-level verb (only active with UI pack), slot signature `navigate to <screen-name>`, type constraint `screen`, execution `set_value` writing `current-screen`. §136 component schemas predefined with freeform overflow. §137 general-purpose pack verb contract: packs JSON declares `vocabulary` (noun additions to the reserved list while loaded) and `verbs` (slot signatures with optional `type_constraint` + an `execution` block whose `type` selects dispatch — `set_value` is the first); pack verbs registered as VERB tokens by the lexer, dispatched after base verbs by the parser, type-checked against record descriptors by the analyzer, and executed by the interpreter; backward-compatible with v3a pack JSON (no `verbs` field). §138 TypeScript port scope — `@mobius/liminate-lang` ports lexer/reorderer/parser/analyzer/renderer (NOT interpreter or listener) with the pack verb contract from day one; the 127 sentences are the sync contract. §139 two-phase build (Phase 1 Python + UI pack, Phase 2 TS port). §140 test sentences 118–127. §141 build boundary; v4a does not build Möbius client, proposal engine, tile interface, or interpreter TS port. Vocabulary unchanged: still **10 verbs, 14 connectives, 34 base reserved words**. `SymbolEntry` gains a `descriptor` field populated by `_exec_remember_record` so `navigate to` can check it.

**Test specification:**

- `liminate_v1_thirty_sentences.md` — Test specification (sentences 1–30 + design questions). Additional sentences 31–34 in v1c §53, 35–48 in v1d §65, 49–59 in v2a §74, 60–68 in v2b §83, 69–80 in v2c §94, 81–95 in v2d §105, 96–113 in v3a §125, 114–117 in v3b §131, 118–127 in v4a §140.

**Reading order for a fresh session:** inception checkpoint → v1a/v1b/v1c/v1d in order → v2a → v2b → v2c → v2d → v3a → v3b → v4a. Each addendum locks decisions on top of all prior; v3b is the first to supersede a sub-decision (v2c §91), with explicit rationale in §127. v4a is the first addendum to extend the pipeline's dispatch tables (parser verb-dispatch, analyzer type-constraint check, interpreter execution dispatch) without changing base vocabulary.

## Commands

```bash
# Print the installed version (reads importlib.metadata at runtime)
liminate --version

# Run all tests (713 passing as of v4a Phase 1 — May 13, 2026)
pytest tests/ -v

# Run a single module's tests
pytest tests/test_lexer.py -v
pytest tests/test_listener.py -v
pytest tests/test_integration_v3a.py -v

# Run the interpreter on a file (Phase 1 sequential)
liminate examples/program1_basics.limn

# Run a file with the canonical-echo suppressed (clean output)
liminate examples/dogfood_1_corpus_summary.limn --quiet

# Test mode (auto-confirms amber outcomes; flags accepted in any position)
liminate examples/program2_orders.limn --test
liminate --test --quiet examples/dogfood_v2a_14_realistic.limn

# Phase 2 event-driven mode: register `when` handlers then drive them
# with a scripted test domain pack (v3a §118). Multiple --pack flags
# accumulate. Pack JSON shape:
#   {"name": "...", "declarations": [["name","type"], ...],
#    "script": [["name", value], ..., "[done]"]}
liminate examples/dogfood_v3a_event_driven.limn \
    --pack examples/dogfood_v3a_pack.json --test --quiet

# Phase 2 event-driven mode with the timer pack (real threaded source).
# Inline JSON config — same flag, `--pack` now also accepts a JSON
# string starting with `{`. The `type` field dispatches to the pack
# factory (`test` is the default for backward compatibility).
liminate examples/dogfood_v3a_timer_pack.limn \
    --pack '{"type": "timer", "interval_ms": 200, "max_ticks": 5}' --quiet

# v4a UI domain pack — pack-level `navigate to <screen>` verb +
# 10 component nouns reserved while the pack is loaded.
liminate --pack examples/pack_ui.json --quiet \
    examples/dogfood_navigate_test.limn

# Interactive REPL (Phase 1 only — REPL doesn't enter listener mode)
liminate

# `python -m liminate ...` is the equivalent module-invocation form
# of every command above (useful when the `liminate` script is not on PATH).
```

## Modules (src/liminate/)

- `lexer.py` — tokenizer + `leading_indent` (v3a §110).
- `vocabulary.py` — verb/connective/operator/article tables +
  `PackVerbSignature`/`PackVerbSlot`/`PackVerbExecution` dataclasses +
  `activate_pack_words`/`deactivate_all_pack_words` for runtime pack
  registration (v4a §137).
- `reorderer.py` — small permutation acceptor (v1d §55).
- `parser.py` — AST + `parse(tokens)` for single statements +
  `parse_when_block(header, action_lines)` for v3a §110 blocks +
  `PackVerbNode` AST + pack-verb dispatch after base verbs (v4a §137).
- `renderer.py` — canonical prose, including multi-line `when` output.
- `analyzer.py` — semantic checks + v3a `in_action_block` /
  `live_value_names` parameters + v4a pack-verb type-constraint
  checking (`_check_pack_verb`) against the record's `descriptor`.
- `interpreter.py` — Phase 1 execution + `HandlerTable` +
  `_FinishRequested` exception + ContextVars for listener context +
  v4a pack-verb dispatch (`_exec_pack_verb`, currently `set_value`).
- `listener.py` — Phase 2 generator (`listen(...)`) — initial
  evaluation, event-queue drain, cascading, cycle detection,
  shutdown.
- `adapter.py` — `DomainPack`, `Adapter`, `TestAdapter`,
  `TestDomainPack`, `LiveValueRegistry` (v3a §116–§120) +
  optional `verbs()` / `vocabulary()` on `DomainPack` and the
  `parse_pack_verb_signature` JSON helper (v4a §137 — backward-
  compatible: packs without these methods/fields keep working).
- `cli.py` — `Session` (owns symtab + handler table + registry +
  packs; resets active pack vocabulary on construction per v4a §137),
  `run_file` (with v3a §110 block buffering and Phase 2 entry),
  `--pack` flag for JSON pack loading (parses optional `vocabulary`
  and `verbs` fields).
- `packs/timer.py` — `TimerAdapter` + `TimerDomainPack` + `make_timer_pack(config)`
  (v3a §116 — first real domain pack; threaded periodic event source).
- `result.py` — `LiminateResult` with nine statuses + metadata.

## Code Style

- Python 3.10+ (for match statements, type unions with `|`)
- Use dataclasses for structured data (Token, AST nodes, SymbolEntry, LiminateResult)
- Use enums for fixed categories (TokenType, ResultStatus)
- Type hints on all function signatures
- Docstrings referencing spec section numbers for non-obvious decisions

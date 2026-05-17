# CLAUDE.md — Liminate Programming Language

## Project Overview

Liminate is a prose-as-syntax programming language designed by Rob Thomas (R. Michael Thomas). You are the builder. Rob is the architect. All design decisions are locked in the specification documents.

**Current state (May 16, 2026):** v1 interpreter + v2a (`keep` verb, `of` connective, multi-field `each show`, descriptor preservation) + UX polish (`--quiet` flag, named-offender error wording, auto-show truncation) + v2.1-patches (duplicate-field rejection, `of`-on-list suggestion, list-operations-only error) + v2b (composition return values, generalized `of`) + v2c (quoting mechanism for multi-word strings) + v2d (composition parameters with `from`, `choose` verb with `if`/`otherwise`) + v3a (event-driven listener mode: `when`/`unless` connectives, `finish` verb, two-phase execution, indentation-based action blocks, adapter contract, cascading triggers, conservative cycle detection) + v3b (quoted-string case preservation: lexer no longer folds case inside quotes; renderer adds case-bearing as a third conditional-quoting trigger) + v4a (general-purpose pack verb contract: packs declare verbs with slot signatures, type constraints, and execution dispatch in JSON; UI domain pack with 10 component nouns and `navigate to <screen-name>`) + liminate-v1-add (`add` verb — append an item to an existing list, with five live-value/type/iterator safety checks) + **liminate-v2 (pack verb contract extension: four new execution types — `substring_check`, `append_to_list`, `set_field`, `compare_values` — plus positional/connective-less slots, per-slot `value_type` declarations, and a target/source resolution model with literal-or-slot-derived dimensions on every write-target type; discriminated execution-class union with `isinstance` dispatch; nine load-time validation rules)**. The Phase 1 pipeline architecture from §8–§9 is unchanged through all extensions; Phase 2 adds a single-threaded event-queue runtime layered on top; v4a/liminate-v2 extend the parser/analyzer/interpreter dispatch tables without changing the base vocabulary. A separate TypeScript port of the validation pipeline (lexer + reorderer + parser + analyzer + renderer; no interpreter) lives in `mobius/packages/liminate-lang/` and validates against this implementation via the 127-sentence sync contract.

**A note on the two version chains.** The `liminate_addendum_v1_*` and `liminate_addendum_v2_*` documents are the first and second addenda of the new `liminate_*` chain that begins after the Inscript→Liminate rename (May 15, 2026). They are NOT successors to the Inscript v1/v2 addenda — those are `liminate_addendum_v1a/b/c/d`, `liminate_addendum_v2a/b/c/d`, etc. (preserved through the rename). When reading, treat `liminate_addendum_v1_add_verb.md` and `liminate_addendum_v2_pack_verb_contract_extension.md` as the post-rename chain endpoints; everything else is upstream.

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

**Liminate addenda (post-rename chain, May 16, 2026):**

- `liminate_addendum_v1_add_verb.md` — **LOCKED + IMPLEMENTED.** Adds `add <item> to <list>` as a base verb (analyzer-enforced live-value, target-is-list, item-resolves, type-compat, and self-mutation-inside-each checks; deep-copy append; the v1 §7 polymorphic `none` seed pattern is preserved). Vocabulary: **11 verbs, 14 connectives, 35 reserved words**. The rationale (`add` as base verb, not pack verb) is that the v4a pack contract — `set_value` only — could not express list-append; this gap motivated the liminate-v2 contract extension that followed.

- `liminate_addendum_v2_pack_verb_contract_extension.md` — **LOCKED + IMPLEMENTED.** Resolves V4-Q1 (execution types beyond `set_value`) and partially resolves V4-Q2 (connective reuse — positional-slot constraint). §1 positional (connective-less) slots: `PackVerbSlot.connective` may be `None`; at most one positional slot per verb, first position, enforced at load. §2 slot value-type declarations: `value_type: "name"` (UNKNOWN→NameRef, default) or `"value"` (any value via `_parse_value` — NUMBER, UNKNOWN, QUOTED_STRING, FieldAccessNode). §3 + §8 nine load-time validation rules (in `_validate_pack_verb_signature`). §4 `substring_check` (case-sensitive containment; error on miss; analyzer requires `against_slot` of type `string`). §5 `append_to_list` (deep-copy append; reuses the v1-add five checks via the factored `_check_list_append`). §6 `set_field` (single-field mutation on a record, creates field if absent, updates `schema`). §7 `compare_values` (`equality` or `structural` mode × `error` or `flag` on mismatch; dual-target output `status_target` + `details_target` with field-name or index lists for structural diffs). §8 target/source resolution model — `set_value`/`append_to_list`/`set_field` all support `target_name | target_slot` (literal vs slot-derived target) and `source_slot | literal_value` (slot value vs fixed literal); exactly-one-of for each pair; `_resolve_target` and `_resolve_source` shared interpreter helpers; `set_value` preserves its existing name-vs-value special case for `source_slot`. §9 discriminated execution-class union — five frozen dataclasses (`SetValueExecution`, `SubstringCheckExecution`, `AppendToListExecution`, `SetFieldExecution`, `CompareValuesExecution`) replace the flat `PackVerbExecution`; `isinstance` dispatch in `interpreter.py` and `analyzer.py`; factory function `_parse_execution` in `adapter.py`. §10 file-by-file changes (vocabulary, adapter, parser, analyzer, interpreter; renderer extends the positional-slot guard). §11 complete JSON schema with examples for `cite` / `verify` / `reveal` / `activate` / `assign`. Vocabulary unchanged from v1-add: **11 verbs, 14 connectives, 35 reserved words**.

**Test specification:**

- `liminate_v1_thirty_sentences.md` — Test specification (sentences 1–30 + design questions). Additional sentences 31–34 in v1c §53, 35–48 in v1d §65, 49–59 in v2a §74, 60–68 in v2b §83, 69–80 in v2c §94, 81–95 in v2d §105, 96–113 in v3a §125, 114–117 in v3b §131, 118–127 in v4a §140.

**Reading order for a fresh session:** inception checkpoint → v1a/v1b/v1c/v1d in order → v2a → v2b → v2c → v2d → v3a → v3b → v4a → liminate-v1-add → liminate-v2 (pack verb contract extension). Each addendum locks decisions on top of all prior; v3b is the first to supersede a sub-decision (v2c §91), with explicit rationale in §127. v4a is the first addendum to extend the pipeline's dispatch tables (parser verb-dispatch, analyzer type-constraint check, interpreter execution dispatch) without changing base vocabulary. liminate-v2 is the first to replace a vocabulary dataclass (the flat `PackVerbExecution` becomes a discriminated union of five frozen dataclasses), but still without touching the 35-word base vocabulary.

## Commands

```bash
# Print the installed version (reads importlib.metadata at runtime)
liminate --version

# Run all tests (809 passing as of the descriptor-propagation fix — May 16, 2026)
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

# liminate-v2 test pack — exercises all five execution types
# (set_value, substring_check, append_to_list, set_field,
# compare_values) plus positional slots and slot-derived targets.
liminate --pack examples/pack_test_execution_types.json --quiet \
    examples/dogfood_v2_execution_types.limn

# Stdin reader pack — each piped line becomes a `line` live-value update.
printf "hello\nworld\n" | liminate examples/dogfood_stdin_echo.limn \
    --pack '{"type": "stdin"}' --quiet

# File watcher pack — polls a directory and emits paired
# (changed-file, change-type) updates for each created/modified/deleted file.
liminate examples/dogfood_file_watcher.limn \
    --pack '{"type": "file-watcher", "path": "./inbox", "max_events": 1}' --quiet

# Interactive REPL (Phase 1 only — REPL doesn't enter listener mode)
liminate

# `python -m liminate ...` is the equivalent module-invocation form
# of every command above (useful when the `liminate` script is not on PATH).

# Build a standalone single-file binary for the current platform
# (PyInstaller, output at dist/liminate). Requires the `build` extra.
./build/build_binary.sh

# Branch G Phase C — compile a Liminate program to a standalone
# executable. Validates the source (lex → reorder → parse) at build
# time, embeds the original source + each --pack JSON + a precomputed
# inspection manifest, and invokes PyInstaller. Reactive programs
# without a pack still build; a one-line notice is printed to stderr.
liminate build demo.limn --output demo
liminate build reactive.limn --pack monitor.json --output reactive

# Inspect a built binary. --inspect surfaces the four §12 sections
# (source / understood-as / packs / vocabulary in use) in plain text;
# --json emits the same data structured. Both paths short-circuit
# before the embedded program executes.
./demo --inspect
./demo --inspect --json
liminate inspect ./demo
liminate inspect ./demo --json

# Release a new version (pushes a v* tag, which triggers
# .github/workflows/release.yml to build macOS / Linux / Windows
# binaries and create a GitHub Release with all three attached).
# See RELEASING.md for the full checklist and required secrets.
git tag v0.x.x
git push origin v0.x.x
```

## Modules (src/liminate/)

- `lexer.py` — tokenizer + `leading_indent` (v3a §110).
- `vocabulary.py` — verb/connective/operator/article tables +
  `PackVerbSignature`/`PackVerbSlot` dataclasses (with `connective:
  str | None` and `value_type` per liminate-v2 §1/§2) + discriminated
  execution-class union `PackVerbExecution = SetValueExecution |
  SubstringCheckExecution | AppendToListExecution | SetFieldExecution
  | CompareValuesExecution` (liminate-v2 §9) +
  `activate_pack_words`/`deactivate_all_pack_words` for runtime pack
  registration (v4a §137). Base vocabulary: 11 verbs, 14 connectives,
  35 reserved words.
- `reorderer.py` — small permutation acceptor (v1d §55).
- `parser.py` — AST + `parse(tokens)` for single statements +
  `parse_when_block(header, action_lines)` for v3a §110 blocks +
  `PackVerbNode` AST + pack-verb dispatch after base verbs (v4a §137).
  liminate-v2: `_parse_pack_verb` handles positional (`connective is
  None`) slots before connective-introduced ones, and routes each slot
  through `_parse_pack_slot_value` per its `value_type` (`"name"` =
  UNKNOWN-only NameRef; `"value"` = `_parse_value` — accepts NUMBER,
  UNKNOWN, QUOTED_STRING, FieldAccessNode).
- `renderer.py` — canonical prose, including multi-line `when` output.
- `analyzer.py` — semantic checks + v3a `in_action_block` /
  `live_value_names` parameters + v4a pack-verb type-constraint
  checking (`_check_pack_verb`) against the entry's `descriptor`
  regardless of underlying type (descriptor-propagation fix removed
  the prior `entry.type == "record"` gate so `type_constraint` works
  on string and list variables too — enables liminate-session-contracts
  SC-Q1's `cite from <source>` on string-typed sources).
  liminate-v2: `_check_pack_verb` extends to `isinstance`-dispatch
  the execution-specific validators `_check_pack_substring` (against
  must be `string`), `_check_pack_append` (delegates to the factored
  `_check_list_append` shared with `_check_add`), `_check_pack_set_field`
  (target must be `record`), and `_check_pack_compare` (both slots
  must resolve to symbol-table names).
- `interpreter.py` — Phase 1 execution + `HandlerTable` +
  `_FinishRequested` exception + ContextVars for listener context +
  v4a pack-verb dispatch (`_exec_pack_verb`). liminate-v2 rewrites
  `_exec_pack_verb` as a five-branch `isinstance` dispatch into
  `_exec_pack_set_value` (preserves the name-vs-value special case for
  `source_slot`), `_exec_pack_substring_check`, `_exec_pack_append_to_list`
  (deep-copy append; handles the v1 §7 `none` polymorphic seed),
  `_exec_pack_set_field` (creates field if absent + updates `schema`),
  and `_exec_pack_compare_values` (equality vs structural — record
  field-diff, list index-diff, length/type mismatch — with
  `on_mismatch: error` or `flag`). Two shared helpers — `_resolve_target`
  and `_resolve_source` — implement the liminate-v2 §8 target/source
  resolution model (literal vs slot-derived for both dimensions).
- `listener.py` — Phase 2 generator (`listen(...)`) — initial
  evaluation, event-queue drain, cascading, cycle detection,
  shutdown.
- `adapter.py` — `DomainPack`, `Adapter`, `TestAdapter`,
  `TestDomainPack`, `LiveValueRegistry` (v3a §116–§120) +
  optional `verbs()` / `vocabulary()` on `DomainPack` and the
  `parse_pack_verb_signature` JSON helper (v4a §137 — backward-
  compatible: packs without these methods/fields keep working).
  liminate-v2: factory `_parse_execution(exec_def)` dispatches on
  the JSON `type` field to one of the five execution dataclasses;
  `_validate_pack_verb_signature(sig)` enforces the nine load-time
  rules (one positional slot, first position; unique connectives on
  required slots; known `value_type` and execution-`type`; exactly-
  one-of for target_name/target_slot and source_slot/literal_value
  on write-target types; `details_target` required for structural
  comparison). Pack JSON that fails validation raises `ValueError`
  at load and never activates.
- `cli.py` — `Session` (owns symtab + handler table + registry +
  packs; resets active pack vocabulary on construction per v4a §137),
  `run_file` (with v3a §110 block buffering and Phase 2 entry),
  `--pack` flag for JSON pack loading (parses optional `vocabulary`
  and `verbs` fields).
- `packs/timer.py` — `TimerAdapter` + `TimerDomainPack` + `make_timer_pack(config)`
  (v3a §116 — first real domain pack; threaded periodic event source).
- `packs/stdin.py` — `StdinAdapter` + `StdinDomainPack` + `make_stdin_pack(config)`.
  Daemon thread reads lines from `sys.stdin` (or an injected stream for tests);
  each line is pushed as `AdapterUpdate(name="line", value=<line>)`; EOF emits
  `AdapterDone`. Pure stdlib.
- `packs/file_watcher.py` — `FileWatcherAdapter` + `FileWatcherDomainPack` +
  `make_file_watcher_pack(config)`. Polls a directory at `poll_interval_ms`
  (default 1000 ms) and emits `changed-file` then `change-type` update pairs
  for created/modified/deleted files (non-recursive; recursive deferred). Pure
  stdlib (`os.scandir` + `st_mtime`). The 4 registered `--pack` factory types
  are now `test`, `timer`, `stdin`, `file-watcher`.
- `result.py` — `LiminateResult` with nine statuses + metadata.
- `build.py` — Branch G Phase C. `build()` validates a source file
  (lex → reorder → parse, composition-name tracking across statements),
  computes the inspection manifest (source + canonical + packs + vocab-
  in-use + version), generates an embedded entry script, and invokes
  PyInstaller. Emits the Q2 reactive-without-adapter notice to stderr
  when applicable.
- `inspect_cmd.py` — Phase C inspection surface. `format_manifest`
  renders the four §12 sections (source / understood-as / packs /
  vocabulary-in-use) as plain text or JSON; used both by the embedded
  entry script's `--inspect` handler and by `liminate inspect <binary>`,
  which shells out to `<binary> --inspect [--json]`.

## Code Style

- Python 3.10+ (for match statements, type unions with `|`)
- Use dataclasses for structured data (Token, AST nodes, SymbolEntry, LiminateResult)
- Use enums for fixed categories (TokenType, ResultStatus)
- Type hints on all function signatures
- Docstrings referencing spec section numbers for non-obvious decisions

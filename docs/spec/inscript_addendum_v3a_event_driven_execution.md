# ADDENDUM
## Inscript Programming Language — Event-Driven Execution
### v3a — The Listener Model

**Status:** LOCKED — EXTENDS `inscript_addendum_v2d_parameters_and_branching.md`
**Date:** May 12, 2026
**Author:** Rob Thomas / R. Michael Thomas (architect) and Claude (builder, drafting)
**Document type:** Addendum — activates `when`/`unless` temporal connectives and adds the `finish` verb, transitioning the interpreter from sequential-only to sequential-plus-reactive execution. Resolves Q13 (event-driven execution model) and closes Branch F.
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** Extends `inscript_addendum_v2d_parameters_and_branching.md` (May 12, 2026), which extends v2c/v2b/v2a/v1d/v1c/v1b/v1a and the Inception Checkpoint v1 (May 11–12, 2026). Continues from §106. Q13 was originally identified in the inception checkpoint (§25) as the "primary v2 engineering question"; it is activated as v3a after v2d completed the sequential feature set. The `when`/`unless` temporal connectives were reserved in inception §11 and deferred through every subsequent addendum. `finish` is new. The ten core architectural decisions were worked out in a dedicated session (May 12, 2026) and refined by twelve architect decisions resolving findings from an external review (ChatGPT, May 12, 2026). This addendum locks those decisions. The v3 series is distinct from v2a–v2d (which built out sequential execution) because this addendum changes the execution model.

---

## HOW TO READ THIS DOCUMENT

- §107 frames the two-phase execution model — the single most important architectural decision.
- §108–§110 specify the `when` verb, `unless` guard, and indentation-based action blocks.
- §111–§112 specify action block scope and the `finish` verb.
- §113–§115 specify edge-triggered evaluation, cascading triggers, and execution ordering.
- §116–§120 specify event sources: adapter contract, live value lifecycle, concurrency model, adapter failure, and domain pack registration.
- §121 specifies initial evaluation.
- §122 specifies the result interface.
- §123 handles amber precedence in `when`/`unless`.
- §124 updates the vocabulary table.
- §125 adds test sentences 96–113 to the test suite.
- §126 extends the build boundary.

---

### §107 — TWO-PHASE EXECUTION MODEL

**Decision: an Inscript program executes in two phases. Phase 1 is sequential (identical to the current v2d interpreter). Phase 2 is reactive (event-driven). A program enters Phase 2 only if Phase 1 completes with zero errors and the handler table is non-empty. LOCKED as the execution model for event-driven Inscript.**

**Phase 1 — Sequential.** The interpreter processes every top-level statement in source order. Sequential statements (`remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each`, `choose`, named composition definitions, named composition calls) execute immediately and produce results identically to the current v2d interpreter. `when` blocks are parsed, validated, and registered in the handler table but not executed. Phase 1 produces results for every executed statement — the same structured `InscriptResult` objects as v2d.

**Phase 2 — Reactive.** If the handler table is non-empty after Phase 1, the interpreter enters listener mode. The Phase 2 startup sequence is:

1. Perform initial evaluation of all registered handlers in registration order (§121).
2. After all initial firings and their cascades resolve, start adapter dispatch (§120).
3. Enter the event loop: dequeue adapter updates, process each to completion.

Phase 2 runs until `finish` is called (§112), all adapters have failed or completed (§119), or external termination (SIGINT).

**Phase 2 gate.** If any Phase 1 statement produces a parse error, semantic error, or unresolved amber outcome, Phase 2 does not start. The interpreter reports all Phase 1 results and terminates. All Phase 1 statements are attempted (stepwise, per v1d §56) — the gate checks the aggregate, not short-circuits on first error. This is stricter than sequential stepwise behavior because a reactive program that enters listener mode with partially-initialized state is dangerous in a way a sequential program with a mid-stream error is not.

**No `when` blocks = no Phase 2.** If the handler table is empty after Phase 1, the interpreter terminates after Phase 1 exactly as v2d does. Every existing v2d program runs unchanged.

**No adapters = auto-shutdown.** If Phase 2 starts but no adapters are registered (no domain pack, no live values), the interpreter performs initial evaluation, then exits cleanly with a shutdown result: `"No event sources registered. Initial evaluation complete."` `finish` during initial evaluation takes precedence over auto-shutdown.

---

### §108 — `WHEN` STATEMENT: GRAMMAR, REGISTRATION, AND CONDITION RESOLUTION

**Decision: `when` is a top-level statement-introducing connective that registers a reactive handler. Its conditions use `choose`-style value-expression resolution (symbol table names, `of` expressions legal). Names in conditions must exist at registration time. LOCKED.**

**Grammar:**

```
when <condition>
  <action-block>

when <condition> unless <guard-condition>
  <action-block>
```

`when` is a top-level statement only. It cannot appear inside named composition bodies (parse error at definition time, applies to all compositions — parameterized or not), inside `each` bodies, or inside another `when` action block. The parser rejects nested `when` at parse time, not semantic analysis time.

**Condition resolution.** `when` conditions use the same value-expression resolution as `choose` conditions (v2d §100), not `where`-clause field resolution. Operands are symbol table names or `<field> of <record>` value expressions. There is no implicit list target. Operators are the same: `is above`, `is below`, `is equal to`, `is not above`, `is not below`, `is not equal to`. Compound conditions with `and`/`or` use the same precedence rules (v1a §30, inception §21).

Example: `when status of patient is equal to discharged` is legal. `status` is a field, `patient` is a symbol table name. The handler watches `patient` (the symbol), not `status` (the field).

**Dependency extraction rule.** For dependency extraction, a value expression of the form `<field> of <record>` depends on `<record>`, not on `<field>`. A bare name depends on itself. Compound conditions (`and`/`or`) collect dependencies from all sub-conditions. The `watching` list in the listener entry marker (§122) reports the union of all dependencies across all registered handlers.

**Registration-time name resolution.** All names referenced in `when` conditions must exist in the symbol table at the point the `when` statement is encountered during Phase 1. This includes names defined by prior sequential statements and live values declared by domain packs (§118). Names defined later in Phase 1 are not visible. This is consistent with every other construct in the language — there are no forward references.

**Registration.** During Phase 1, the parser fully parses the `when` condition, optional `unless` guard, and action block into AST nodes. The semantic analyzer validates all names, types, and operator compatibility at registration time. If validation succeeds, the handler is added to the handler table. If it fails, the error is a Phase 1 error and prevents Phase 2 (§107).

**Action block parsing.** All statements in the action block are fully parsed at registration time. Parse errors in action blocks are Phase 1 errors. Name resolution within action blocks occurs at firing time against the current symbol table (§111), not at registration time, because actions may reference values created by other handlers or adapter updates.

---

### §109 — `UNLESS` GUARD CLAUSE

**Decision: `unless` is a guard clause on `when`, not a standalone construct. The compound eligibility is: when-condition is true AND unless-condition is false. Edge triggering applies to the compound state. LOCKED.**

`unless` appears between the `when` condition and the action block:

```
when blood-pressure is above 180 unless medication-given is equal to true
  show "alert"
```

The handler fires when the compound eligibility (when-true AND unless-false) transitions from false to true. If the `when` condition is true but the `unless` condition is also true, the handler does not fire. If the `unless` condition later becomes false while the `when` condition remains true, the compound eligibility transitions to true and the handler fires.

**Condition resolution.** `unless` conditions use the same `choose`-style value-expression resolution as `when` conditions (§108). All referenced names must exist at registration time. `of` expressions are legal.

**Delimiter behavior.** `unless` splits the condition line into two independent condition ASTs. Precedence is resolved separately inside each AST. The final eligibility is `when_ast AND NOT unless_ast`. Mixed `and`/`or` within either AST triggers amber independently (§123).

**Dependency extraction.** Both `when` condition and `unless` guard references are watched. A change to any referenced value in either part triggers re-evaluation of the compound eligibility.

---

### §110 — INDENTATION-BASED ACTION BLOCKS

**Decision: `when` action blocks use indentation-based block structure. Minimum one space, tabs rejected, block ends at next unindented line or EOF. LOCKED.**

This is the first block structure in Inscript. Every prior construct has been single-line (with `and` for operation sequencing and `:` for composition bodies and `choose` branches). `when` action blocks need multi-line structure because action blocks can contain `choose` with `otherwise`, multi-statement sequences, and composition calls that would be unreadable on one line.

**Rules:**

- Any line indented at least one space after a `when` line belongs to that handler's action block.
- All lines in a block must use the same indentation depth (the depth of the first indented line sets it for the block).
- The block ends at the first non-blank line with indentation less than the block depth, including zero indentation (a top-level statement).
- Blank lines inside a block are skipped (consistent with v1c §48).
- Tabs are rejected at the lexer level with a clear error suggesting spaces.
- An empty block (a `when` line followed immediately by an unindented line or EOF) is a parse error.
- Indentation deeper than the block's established depth is a parse error. All action-block lines must match the first line's depth exactly. This prevents hidden structural ambiguity.
- The colon after the `when` condition line is optional. Present or absent, the indented block is what defines the action scope. (The colon continues to be required for `choose` and composition definitions, which are single-line constructs.)

**Multi-statement action blocks.** Each indented line is a separate statement. Statements within a line can also use `and` for operation sequencing (existing rule 3). Both forms are legal:

```
when temperature is above 100
  show "alert"
  remember a flag called overheating with true

when temperature is above 100
  show "alert" and remember a flag called overheating with true
```

Both produce the same behavior. The multi-line form is preferred for readability.

---

### §111 — ACTION BLOCK SCOPE

**Decision: all v2d verbs, composition calls (including parameterized), and `finish` are legal inside `when` action blocks. `remember` cannot overwrite live adapter-owned values. `filter` (destructive) on live values is disallowed. `when` inside `when` is prohibited. LOCKED.**

**Legal inside action blocks:**

- All sequential verbs: `remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each`, `choose`.
- Named composition calls, including parameterized calls (`comp from name`) and value-capturing calls (`remember ... from comp from name`).
- Named composition definitions (`remember how to ...`). Definitions commit immediately like any `remember` statement — they are available to subsequent statements in the same block, cascaded handlers, later handlers, and future firings.
- `finish` (§112).

**Prohibited inside action blocks:**

- `when` (top-level only, §108).

**Restrictions on live values (Phase 2 ownership):**

- `remember` targeting a live-value name inside an action block is a semantic error: `"<name> is a live value provided by the domain pack and cannot be overwritten during listener mode."` Phase 1 `remember` may initialize live values (§117).
- `filter` targeting a live-value name is a semantic error in all contexts (same reason — `filter` is destructive).
- `keep` targeting a live-value name is legal (`keep` is non-destructive — it returns a new list without modifying the source).
- `show`, `count`, `combine`, `each` targeting live-value names are legal (read-only or non-destructive).

**`choose` inside action blocks.** Legal, subject to v2d rules: `choose` is side-effect-only (v2d §102), cannot appear inside `each` (v2d §102). `choose` inside `each` inside a `when` action block is doubly prohibited — by the `each` restriction, not a new `when` restriction.

**Statement execution.** Action block statements execute in order using stepwise semantics (v1d §56). Each statement commits independently. A non-fatal error on one statement does not prevent subsequent statements from executing. The handler remains active after a non-fatal action error.

**Name resolution timing.** Action block statements are parsed at registration time but names within them are resolved at firing time against the current symbol table. This is because actions may reference values created after the handler was registered — by other handlers, adapter updates, or cascaded effects. Statically illegal constructs (nested `when`, `finish` outside action context) are caught at registration/parse time.

**Composition return values.** Action block statements use identical result behavior to sequential mode. Value-returning composition calls auto-show when standalone. `remember ... from comp` captures the return value. The behavior is the same as Phase 1; the action block is just a different execution context, not a different language.

---

### §112 — `FINISH` VERB

**Decision: `finish` is a new verb that exits listener mode. It is immediate and total — no further statements, cascades, handlers, or queued updates execute after `finish`. LOCKED.**

`finish` is valid only inside a `when` action block (directly or inside a composition called from an action block). `finish` in Phase 1 (sequential mode) is a semantic error: `"finish can only be used inside an event handler."` 

**Immediate and total.** Once `finish` executes:

- No remaining statements in the current action block execute.
- No remaining cascades from the current handler's modifications are processed.
- No sibling handlers eligible from the same event are evaluated.
- No queued adapter updates are dequeued.
- Adapters are stopped.
- The interpreter yields a shutdown result and terminates.

This applies regardless of where `finish` appears:

- **Inside a `choose` branch in an action block:** the `choose` exits, the action block exits, the listener exits.
- **In a cascaded handler:** the cascade chain terminates, pending handlers are skipped, the listener exits.
- **Inside a composition called from an action block:** the composition exits, the calling action block exits, the listener exits.

**`finish` in compositions.** `finish` may appear inside named composition bodies. It is not an error at definition time. However, if the composition is called during Phase 1 (sequential mode), `finish` produces a semantic error at call time: `"finish can only be used inside an event handler."` If the composition is called from a `when` action block, `finish` executes normally and terminates the listener.

**Precedence with non-fatal errors.** Non-fatal action errors do not prevent `finish` from executing. If a statement before `finish` in the same action block errors, subsequent statements (including `finish`) still execute per stepwise semantics. Once `finish` executes, it takes immediate effect regardless of prior errors.

**`finish` yields only the shutdown result.** `finish` does not yield a separate action-statement result. The shutdown result (§122) is the only result produced by `finish`.

**`finish` is side-effect-only.** A composition whose last operation is `finish` has no return value. Using such a composition in value position (`remember ... from <comp>`) is a semantic error at the call site, per v2b §76.

---

### §113 — EDGE-TRIGGERED EVALUATION AND CHANGE DETECTION

**Decision: `when` handlers are edge-triggered — they fire on false-to-true transition of their compound eligibility. Change detection uses deep value equality. Unset live values evaluate as condition-false. Unchanged adapter updates produce no re-evaluation. LOCKED.**

**Edge triggering.** A handler fires when its compound eligibility (when-condition AND NOT unless-condition) transitions from false to true. A condition that is already true and remains true does not fire again. A condition that becomes false and then becomes true again fires on the second transition.

**Change detection.** An adapter update or `remember` statement that modifies a watched value triggers re-evaluation of all handlers referencing that name. "Modification" means the new value differs from the stored value under Inscript value equality:

- Numbers: numeric equality.
- Strings: string equality (case-normalized per v1c, §22).
- Lists: deep equality — same length, same items in same order, each item recursively equal.
- Records: deep equality — same fields with same values.

If the new value is equal to the stored value, the update is absorbed silently — the symbol table value is unchanged, no handlers are re-evaluated, no results are emitted. This is not Python object identity; it is Inscript value equality.

**Unset live values.** A live value declared by a domain pack but not yet updated (no Phase 1 `remember`, no adapter update received) is "unset." Any comparison involving an unset operand evaluates as false. The condition is not an error — it is simply not yet satisfiable. Once the first adapter update provides a value, normal comparison semantics apply. The first update always triggers re-evaluation because the transition from unset to any value is always a change.

**Cascade-triggering modifications.** Only symbol-table writes count as modifications for cascade evaluation:

- `remember` (stores a value).
- `filter` (mutates a list in place).
- `gather` (stores a new list).

Pure returned values that are only shown or used as intermediate computations do not cascade. `keep` (non-destructive) returns a new value — it only cascades if the returned value is captured via `remember ... from keep`.

**Modification coalescing.** If an action block modifies the same symbol name multiple times (e.g., via `each` sub-operations), modifications are coalesced by symbol name. After the action block completes, each modified name is evaluated once using its final value. Intermediate values are not individually evaluated for cascading.

---

### §114 — CASCADING TRIGGERS AND CYCLE DETECTION

**Decision: cascades resolve depth-first after each action block completes. Cycle detection is conservative: the same handler firing twice in one cascade chain is an error. LOCKED.**

**Cascade mechanism.** When an action block completes, the interpreter checks which symbol-table values were modified during the block. For each modified value, all handlers referencing that value are re-evaluated. If any handler's compound eligibility transitioned from false to true, it fires. This may modify additional values, triggering further cascades.

**Depth-first resolution.** Cascades resolve immediately after the triggering action block, before any sibling handlers from the original event are evaluated. A cascaded handler gets its complete turn — full action block plus its own cascades — before control returns to the next eligible handler at the original level.

**Cycle detection.** If the same handler would fire a second time within a single cascade chain, it is a cycle. The interpreter produces a runtime error with a traced cycle path showing the chain of handlers and value modifications that led to the repeated firing. The error is non-fatal to the listener — it prevents the cycle from executing but other handlers remain active for future events.

This is a conservative cycle guard. A legitimate scenario where handler A fires, its action makes A's condition false, then a later cascade makes it true again, would be flagged as a cycle even though it might terminate. This conservatism is deliberate for v3a — it prevents infinite loops at the cost of disallowing some theoretically-safe patterns. More sophisticated state-based cycle detection can be explored in a future version if concrete use cases demand it.

**Non-fatal action errors do not suppress cascades.** If an action block contains a non-fatal error on one statement, cascades from successful mutations in the same block still fire. The erroring statement is reported but does not prevent the successfully-modified values from triggering their dependent handlers.

---

### §115 — EXECUTION ORDERING AND HANDLER TURNS

**Decision: handlers fire in registration order (top to bottom in program source). Each handler gets its complete turn — action block plus cascades — before the next eligible handler fires. LOCKED.**

When a single value update makes multiple handlers eligible, they fire in the order they were registered during Phase 1. Each handler's action block executes fully, and its cascades resolve fully, before the next eligible handler begins. This guarantees deterministic ordering given the same program and the same event sequence.

---

### §116 — EVENT SOURCES: ADAPTER CONTRACT

**Decision: domain packs provide event sources via a three-part adapter contract: declaration, adapter, and lifecycle. LOCKED.**

**Declaration.** A domain pack declares which values it will provide as live values, including name and expected type (number, string, list, or record). Declarations are registered before Phase 1 begins — live value names are visible in the symbol table from the start of Phase 1 (required by §108 registration-time resolution). Declared values start as "unset" (§113).

**Adapter.** A Python class that produces `(name, new_value)` pairs. Adapters run in background threads or async tasks but interact with the interpreter only by enqueuing updates into the event queue (§120). Each adapter may only push updates for names it declared. An adapter pushing an update for an undeclared name is an adapter error — the interpreter stops that adapter under adapter isolation rules (§119).

**Value type validation.** The declared type is authoritative. The first update must match the declared type. For broad collection declarations (`list` or `record` without schema detail), the first update establishes the specific schema shape (e.g., which fields a record contains); subsequent updates must match that shape. A type-incompatible update is an adapter error — the update is rejected, the adapter is stopped, and an error result is emitted. The live value retains its previous value.

**Lifecycle.** Adapters are started after initial evaluation completes (§107). Adapters are stopped when `finish` executes, when all adapters have failed, or on external termination. The adapter contract includes `start()` and `stop()` methods.

**Multiple adapters for the same value.** Disallowed in v3a. Two adapters declaring the same live-value name is a startup error — the interpreter reports the conflict and does not enter Phase 2.

---

### §117 — LIVE VALUE LIFECYCLE

**Decision: live values are declared by domain packs, start unset, receive updates from adapters, and are adapter-owned after Phase 2 begins (cannot be overwritten by `remember` inside action blocks). Phase 1 `remember` may provide an initial value for a declared live value. LOCKED.**

A live value's lifecycle:

1. **Declaration.** Domain pack declares `(name, type)` before Phase 1. Symbol table entry created with type but no value (unset).
2. **Phase 1 initialization (optional).** A Phase 1 `remember` statement may provide an initial value for a declared live value. The value must match the declared type. This supports the natural pattern of setting initial state before entering listener mode. The live value transitions from unset to set.
3. **Phase 1 visibility.** The name exists in the symbol table — `when` conditions can reference it at registration time. Comparisons involving unset values evaluate as false; initialized values compare normally.
4. **Initial evaluation.** After Phase 1, handlers are evaluated. Handlers watching unset live values evaluate as false (their conditions cannot be true yet). Handlers watching initialized live values evaluate normally.
5. **Adapter dispatch.** After initial evaluation, adapters start pushing updates. Updates modify the value (subject to change detection, §113). The adapter takes ownership — from this point, user `remember` inside action blocks cannot overwrite the value.
6. **Adapter failure.** If the owning adapter fails, the live value becomes inactive. Handlers depending solely on inactive live values are disabled — they will not fire again. An error result is emitted listing the disabled handlers. If other adapters remain active, the interpreter continues with the remaining handlers.

**Ownership.** Live values are adapter-owned after Phase 2 begins:

- `remember` targeting a live-value name inside a `when` action block is a semantic error (§111).
- `remember` targeting a live-value name during Phase 1 is legal (initial value setup).
- `filter` targeting a live-value name is a semantic error in all contexts (§111).
- `keep`, `show`, `count`, `combine`, `each` may read live values (non-destructive).

---

### §118 — DOMAIN PACK REGISTRATION

**Decision: domain packs are supplied to the interpreter as a constructor parameter or CLI flag, not via language syntax. LOCKED as the v3a registration mechanism.**

Domain pack activation syntax (an Inscript-level `use` or `load` command) is deferred. In v3a, the active domain pack list is provided externally:

- **CLI:** `python -m inscript program.insc --pack healthcare` (or similar flag syntax).
- **API:** `Interpreter(source, domain_packs=[HealthcarePack()])`.
- **Test harness:** test adapter injected via the same API path.

The interpreter receives a list of domain pack objects at construction time. Each pack provides its declarations (live value names and types) and its adapter instance. The interpreter validates declarations (no duplicate names across packs, §116), registers live values in the symbol table, and stores adapters for Phase 2 startup.

**Test adapter.** A special adapter that yields a finite, scripted sequence of `(name, value)` pairs. The test adapter enables deterministic testing of event-driven programs. Notation in test sentences uses `[name = value]` for adapter updates and `[done]` for adapter completion. Normal completion is distinct from adapter failure — only adapters that explicitly signal normal completion (by exhausting their update sequence or calling a completion method) count toward normal shutdown. When all adapters have signaled normal completion, the interpreter exits with a shutdown result.

---

### §119 — ADAPTER CONCURRENCY: SINGLE-THREADED EVENT QUEUE

**Decision: adapters enqueue updates into a thread-safe FIFO queue. The interpreter processes one update to completion before dequeuing the next. LOCKED as the v3a concurrency model.**

Adapters run in background threads (or async tasks). Their only interaction with the interpreter is appending `(name, new_value)` pairs to a shared, thread-safe queue. The interpreter's event loop is single-threaded:

1. Dequeue one `(name, new_value)` pair.
2. Compare new value to stored value (§113 change detection).
3. If changed: write to symbol table, re-evaluate all handlers referencing that name, fire eligible handlers with complete-turn semantics (§115), resolve all cascades.
4. After all handler turns and cascades for this update complete, dequeue the next update.

No interleaving. No concurrent handler execution. The result stream is fully reproducible given the same update sequence. A handler that runs for a long time blocks all other updates from processing — this is acceptable for v3a because Inscript programs are small data operations.

---

### §120 — ADAPTER FAILURE AND ISOLATION

**Decision: adapter failures are isolated. A single adapter crash does not kill the interpreter. LOCKED.**

If an adapter throws an exception, pushes an undeclared name, or pushes a type-incompatible value:

1. The interpreter stops that adapter.
2. An error result is emitted identifying the failed adapter and reason.
3. All live values owned by the failed adapter become inactive (§117).
4. Handlers depending solely on inactive live values are disabled.
5. The interpreter continues with remaining active adapters and handlers.

If the last active adapter fails or completes, the interpreter exits with a shutdown result. If no handlers remain active (all disabled due to adapter failures), the interpreter exits with an error result.

---

### §121 — INITIAL EVALUATION

**Decision: initial evaluation is the first act of Phase 2. It processes all registered handlers in registration order with the same complete-turn semantics as normal event processing. LOCKED.**

After Phase 1 completes and before adapters start dispatching, the interpreter evaluates every registered handler's compound eligibility against the current symbol table state.

**Procedure:**

1. For each handler in registration order: evaluate compound eligibility (when-condition AND NOT unless-condition).
2. If eligible (compound is true): fire the handler — execute action block, resolve cascades, using complete-turn semantics (§115).
3. Cascades during initial evaluation work identically to event-driven cascades — a handler's action may modify values that trigger other handlers.
4. `finish` during initial evaluation terminates the interpreter immediately (§112). Adapters are never started.
5. After all initially-eligible handlers have fired (and all cascades resolved), initial evaluation is complete.

**Trigger metadata for initial evaluation.** Initial-evaluation firings use `trigger.source = "initial"` (§122), distinguishing them from adapter-triggered firings.

---

### §122 — RESULT INTERFACE

**Decision: the listener-mode result interface is a Python generator yielding structured result objects in four phases. LOCKED.**

The event loop yields results via a Python generator, extending the v2d `InscriptResult` contract.

**Phase 1 results.** Identical to v2d — one `InscriptResult` per executed statement. Sequential statements use existing statuses (`success`, `amber`, `error_parse`, `error_semantic`).

**Listener entry marker.** Yielded when Phase 2 begins:

```python
InscriptResult(
    status="listening",
    output=None,
    canonical=None,
    metadata={"watching": ["temperature", "humidity", ...]}
)
```

The `watching` list contains all symbol names referenced by registered handlers (both `when` conditions and `unless` guards). Live values are in `metadata`, not `output`, to avoid confusion with user-visible program output.

**Handler firing results.** Each handler firing yields one result per action-block statement, wrapped in trigger metadata:

```python
InscriptResult(
    status="handler_fire",
    output="alert",  # the statement's output, if any
    canonical="show \"alert\"",
    metadata={
        "trigger": {
            "source": "initial" | "adapter_update" | "cascade",
            "handler_index": 0,
            "values_changed": ["temperature"],  # list, not single value
            "new_values": {"temperature": 105}
        }
    }
)
```

For initial evaluation, `source` is `"initial"` and `values_changed` may be empty (the handler was eligible due to Phase 1 state, not a value change). For cascades, `source` is `"cascade"` and `values_changed` lists the names modified by the prior action block that made this handler eligible.

Action-statement results within a single handler firing share the same trigger metadata. Each statement produces its own result — auto-show, explicit show, error, etc. — with the trigger envelope attached.

**Shutdown result.** Final result yielded when the interpreter exits:

```python
InscriptResult(
    status="shutdown",
    output="Program stopped.",  # or descriptive message
    canonical=None,
    metadata={
        "reason": "finish" | "adapter_complete" | "external" | "no_adapters" | "error",
        "handler_index": 2  # which handler called finish, if applicable
    }
)
```

**Listener-specific statuses.** v3a adds four new result statuses to the existing set:

| Status | Meaning |
|---|---|
| `listening` | Listener entry marker |
| `handler_fire` | Action-statement result during handler execution |
| `shutdown` | Listener termination |
| `error_runtime` | Runtime error during listener mode (cycle detection, adapter failure) |

The existing statuses (`success`, `amber_precedence`, `amber_ambiguity`, `error_parse`, `error_semantic`) continue to apply in Phase 1 and within action-statement results. `error_runtime` is new and covers listener-specific runtime errors: cycle detection (§114), adapter errors (§120), and adapter type mismatches (§116). The five-outcome taxonomy (v1c §50) is extended by one outcome for listener mode.

---

### §123 — AMBER PRECEDENCE IN `WHEN`/`UNLESS`

**Decision: mixed `and`/`or` precedence in `when` and `unless` conditions triggers amber at registration time during Phase 1. LOCKED.**

The existing amber rule (v1a §30) applies to `when` and `unless` conditions identically to how it applies to `where` and `choose` conditions. If a `when` or `unless` condition contains mixed `and`/`or`, the parser shows its interpretation and the user confirms during Phase 1, at the point the `when` statement is encountered.

- In interactive mode: the interpreter displays the parsed interpretation and waits for user confirmation before registering the handler.
- In `--test` mode: amber is auto-confirmed (existing behavior).
- An unresolved amber prevents handler registration, which is a Phase 1 error, which prevents Phase 2 (§107).

Amber fires independently for the `when` condition and the `unless` guard — each is a separate condition AST with its own precedence resolution.

---

### §124 — VOCABULARY UPDATE

**v3a adds one verb and moves two connectives from deferred to active.**

| Category | Words | Count |
|---|---|---|
| **Verbs** | `remember`, `show`, `filter`, `keep`, `count`, `gather`, `combine`, `each`, `choose`, `finish` | **10** |
| **Connectives** | `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as`, `of`, `if`, `otherwise`, `when`, `unless` | **14** |
| **Operators** | `is`, `above`, `below`, `equal`, `not` | **5** |
| **Articles** | `the`, `a`, `an` | **3** |
| **Delimiter** | `:` | **1** |

**Total reserved words: 34** (was 33 in v2d). `finish` is new. `when` and `unless` were already in the reserved word list as V2_RESERVED in v2d (counted in the 33); they now move to active connectives. Adding `finish` brings the total to 34.

**Deferred verbs:** `transform`, `compare`. Reserved-word slots protected, no grammar specified.

---

### §125 — TEST SENTENCES (96–113)

Eighteen new test sentences extending the test suite from 95 (v2d §105).

**Test notation convention.** Event-driven test sentences use the following notation:

- `Test adapter declares: <name> as <type> [, ...]` — the test adapter's domain pack declares these live values. Names are visible in the symbol table from the start of Phase 1 (unset until first update).
- `[name = value]` — the test adapter pushes this update during Phase 2.
- `[done]` — the test adapter signals normal completion.
- When a test sentence uses `remember` to initialize a name that the adapter also declares, Phase 1 initialization is legal (§117). The adapter takes ownership after Phase 2 begins.
- When a test sentence has no adapter declaration line, all names are ordinary symbol-table entries and the test adapter updates those names directly (the test adapter declares them implicitly).

**Sentence 96 — Basic `when` handler fires on condition met.**

```
remember a number called temperature with 50
when temperature is above 100
  show "hot"
```

Test adapter: `[temperature = 105]`

Expected: handler fires, output `hot`.

**Sentence 97 — `when` with `unless` guard suppresses firing.**

```
remember a number called temperature with 50
remember a string called silenced with false
when temperature is above 100 unless silenced is equal to true
  show "alert"
```

Test adapter: `[silenced = true], [temperature = 105]`

Expected: no output. Temperature exceeds 100 but `silenced` is `true`, so the guard suppresses firing.

**Sentence 98 — `finish` exits listener mode.**

```
remember a number called count with 0
when count is above 2
  finish
```

Test adapter: `[count = 1], [count = 3]`

Expected: first update — no output (1 is not above 2). Second update — shutdown: handler fires `finish`.

**Sentence 99 — Multi-statement action block.**

```
remember a number called level with 0
when level is above 50
  show "high"
  remember a string called status with active
```

Test adapter: `[level = 75]`

Expected: output `high`, then `status` stored as `active`.

**Sentence 100 — Cascading triggers.**

```
remember a number called temperature with 0
remember a string called alert with none
when temperature is above 100
  remember a string called alert with triggered
when alert is equal to triggered
  show "cascade fired"
```

Test adapter: `[temperature = 105]`

Expected: first handler fires (temperature > 100), sets `alert` to `triggered`. Cascade: second handler fires (alert = triggered), output `cascade fired`.

**Sentence 101 — Cycle detection error.**

```
remember a number called a with 0
remember a number called b with 0
when a is above 0
  remember a number called b with 1
when b is above 0
  remember a number called a with 1
```

Test adapter: `[a = 1]`

Expected: first handler fires, sets `b` to 1. Cascade: second handler fires, sets `a` to 1. Cascade: first handler would fire again — cycle detected. Runtime error with cycle path.

**Sentence 102 — Initial evaluation fires for already-true conditions.**

```
remember a number called level with 75
when level is above 50
  show "already high"
```

No adapter needed (auto-shutdown after initial evaluation per §107).

Expected: initial evaluation fires handler (level is 75, above 50), output `already high`. Shutdown: no event sources.

**Sentence 103 — `when` with compound condition.**

```
remember a number called temperature with 0
remember a number called humidity with 0
when temperature is above 100 and humidity is above 80
  show "dangerous"
```

Test adapter: `[temperature = 105], [humidity = 85]`

Expected: first update — temperature above 100 but humidity is 0 (not above 80), no output. Second update — both conditions met, handler fires, output `dangerous`.

**Sentence 104 — `when` with `of` expression (choose-style).**

```
remember a record called patient with name as john and status as stable
when status of patient is equal to critical
  show "alert"
```

Test adapter: `[patient = {name: john, status: critical}]`

Expected: adapter updates `patient` record. `status of patient` evaluates to `critical`. Handler fires, output `alert`.

**Sentence 105 — Parameterized composition called from action block.**

```
remember a list called readings with 10 and 20 and 30
remember how to find-high from data: keep the data where each is above 15
remember a number called trigger with 0
when trigger is above 0
  remember the result called high-readings from find-high from readings
  show high-readings
```

Test adapter: `[trigger = 1]`

Expected: handler fires, calls `find-high` with `readings` as parameter, captures result, shows `20, 30`.

**Sentence 106 — `choose` inside `when` action block.**

```
remember a number called temperature with 0
remember a string called mode with normal
when temperature is above 100
  choose if mode is equal to silent: show "logged" otherwise show "alert"
```

Test adapter: `[temperature = 105]`

Expected: `mode` is `normal` (not `silent`), so `otherwise` branch fires, output `alert`.

**Sentence 107 — `finish` inside `choose` branch is immediate and total.**

```
remember a number called temperature with 0
remember a string called critical with false
when temperature is above 100
  choose if critical is equal to true: finish otherwise show "warning"
  show "after choose"
```

Test adapter: `[temperature = 105]`

Expected: `critical` is `false`, so `otherwise` branch fires, output `warning`. Then `show "after choose"` fires, output `after choose`. (Note: `finish` is in the non-taken branch, so it does not execute.)

Second test: same program but `remember a string called critical with true` in Phase 1.

Test adapter: `[temperature = 105]`

Expected: `critical` is `true`, so `finish` fires. No output — `finish` is immediate and total. Shutdown.

**Sentence 108 — Unset live value evaluates as condition-false.**

```
when humidity is above 80
  show "humid"
```

Domain pack declares `humidity` as live number. Test adapter: `[humidity = 85]`

Expected: during initial evaluation, `humidity` is unset — condition false, no firing. After adapter update (85 > 80), handler fires, output `humid`.

**Sentence 109 — Unchanged value produces no re-evaluation.**

```
remember a number called level with 50
when level is above 40
  show "high"
```

Test adapter: `[level = 50], [level = 60]`

Expected: initial evaluation fires (50 > 40), output `high`. First adapter update (50 → 50) — unchanged, no re-evaluation. Second adapter update (50 → 60) — changed, re-evaluation, but condition was already true and remains true — no false-to-true transition, no firing. (Edge trigger: already true → still true = no fire.)

**Sentence 110 — `remember` cannot overwrite live value.**

```
when temperature is above 100
  remember a number called temperature with 0
```

Domain pack declares `temperature` as live number.

Expected: semantic error at registration time: `"temperature is a live value provided by the domain pack and cannot be overwritten."` Phase 1 error prevents Phase 2.

**Sentence 111 — No adapters, auto-shutdown after initial evaluation.**

```
remember a number called x with 10
when x is above 5
  show "yes"
```

No domain pack, no adapters.

Expected: initial evaluation fires (10 > 5), output `yes`. Shutdown: `"No event sources registered. Initial evaluation complete."`

**Sentence 112 — `finish` in composition called from handler.**

```
remember how to emergency-stop: finish
remember a number called level with 0
when level is above 100
  emergency-stop
  show "after stop"
```

Test adapter: `[level = 150]`

Expected: handler fires, calls `emergency-stop`, which executes `finish`. Immediate total shutdown. `show "after stop"` does not execute.

**Sentence 113 — Phase 1 error prevents Phase 2.**

```
when temperature is above 100
  show "hot"
show missingname
```

Domain pack declares `temperature` as live number.

Expected: handler registers successfully. `show missingname` is a semantic error (`missingname` not defined). Phase 1 error prevents Phase 2. No listener mode entered.

---

### §126 — BUILD BOUNDARY

**What v3a builds:**

- Two-phase execution model (§107).
- `when` verb with `choose`-style conditions and registration-time validation (§108).
- `unless` guard clause (§109).
- Indentation-based action blocks (§110).
- Action block scope rules including live-value restrictions (§111).
- `finish` verb with immediate-and-total semantics (§112).
- Edge-triggered evaluation with deep value equality and unset/unchanged semantics (§113).
- Cascading triggers with conservative cycle detection (§114).
- Registration-order execution with complete-turn semantics (§115).
- Adapter contract: declaration, adapter, lifecycle (§116).
- Live value lifecycle: declaration, unset, update, inactive (§117).
- Domain pack registration via constructor/CLI (§118).
- Single-threaded event queue (§119).
- Adapter failure isolation (§120).
- Initial evaluation before adapter dispatch (§121).
- Listener-mode result interface with four new statuses (§122).
- Amber at registration time for `when`/`unless` (§123).
- Test adapter for deterministic event-driven testing.
- CLI support for `--pack` flag (or equivalent).
- Eighteen new test sentences (96–113).

**What v3a does NOT build:**

- Domain pack activation via language syntax (a `use` or `load` verb). Registration is external in v3a.
- Timer grammar in a core domain pack. The test adapter is the only shipped adapter.
- Real-world domain packs (healthcare, smart home, game). These are product work, not language work.
- `transform` or `compare` verbs (deferred, reserved-word slots protected, §103 from v2d).
- `choose` inside `each` (deferred, v2d §102).
- `when` inside `when` (prohibited, §108).
- `when` inside compositions (prohibited, §108).
- `when` inside `each` (prohibited — top-level only).
- Sophisticated cycle detection beyond the conservative same-handler rule (§114).
- Adapter timeout or preemption (§119 — long-running handlers block the queue; acceptable for v3a).
- Tile interface, proposal engine, domain packs as product surfaces (Branch C/E).

---

## WHAT IS LOCKED

This addendum locks:

- **Two-phase execution model (§107).** Phase 1 sequential (v2d-identical), Phase 2 reactive. Phase 2 gated on zero Phase 1 errors. No `when` = no Phase 2. No adapters = auto-shutdown after initial evaluation.
- **`when` statement (§108).** Top-level only. `choose`-style conditions. Registration-time name resolution. Full parse and semantic validation at registration.
- **`unless` guard clause (§109).** Guard on `when`, not standalone. Compound eligibility = when-true AND unless-false. Edge-triggered on compound state. Delimiter splits into independent condition ASTs.
- **Indentation-based action blocks (§110).** Minimum one space, tabs rejected, same depth throughout (deeper is parse error), block ends at lesser indentation or EOF, colon optional, empty blocks are parse errors.
- **Action block scope (§111).** All v2d verbs + `finish` legal. `remember`/`filter` on live values prohibited inside action blocks (Phase 2 ownership). Composition definitions commit immediately. Name resolution at firing time. Result behavior identical to sequential mode.
- **`finish` verb (§112).** Immediate and total. Legal in compositions (semantic error if called outside listener context). Yields only shutdown result.
- **Edge-triggered evaluation (§113).** False-to-true transition. Deep value equality for change detection. Unset = false. Unchanged = no re-evaluation. Only symbol-table writes cascade. Modifications coalesced by name after action block completes.
- **Cascading triggers (§114).** Depth-first. Conservative cycle detection (same handler twice = error). Non-fatal errors don't suppress cascades.
- **Execution ordering (§115).** Registration order. Complete-turn semantics.
- **Adapter contract (§116).** Declaration (name + type), adapter (enqueue updates), lifecycle (start/stop). No duplicate live-value providers. Undeclared pushes = adapter error. Type mismatches = adapter error.
- **Live value lifecycle (§117).** Adapter-owned after Phase 2 begins. Phase 1 `remember` may initialize. Cannot be overwritten by `remember` inside action blocks. Inactive after adapter failure.
- **Domain pack registration (§118).** Constructor/CLI, not language syntax.
- **Single-threaded event queue (§119).** One update to completion before next dequeue.
- **Adapter isolation (§120).** Single failure doesn't kill interpreter. Dependent handlers disabled.
- **Initial evaluation (§121).** Before adapters dispatch. Registration order. Complete-turn semantics. `finish` during initial evaluation prevents adapter start.
- **Result interface (§122).** Four new statuses: `listening`, `handler_fire`, `shutdown`, `error_runtime`. Trigger metadata with `source`, `values_changed`, `new_values`. Shutdown metadata with `reason`.
- **Amber at registration (§123).** Same rules as `where`/`choose`. Fires during Phase 1. Unresolved amber prevents Phase 2.
- **Vocabulary (§124).** 10 verbs (+`finish`), 14 connectives (`when`/`unless` activated), 34 reserved words.
- **Eighteen test sentences (§125).** Sentences 96–113.

This addendum does NOT modify any prior locked decision. Specifically:
- `filter` remains destructive (inception §24).
- `keep` remains non-destructive (v2a §67).
- `combine` remains numeric-only and non-destructive (v1b §38, §39).
- Composition return values (v2b §76) are unchanged — `finish` added to side-effect-only list.
- Composition parameters (v2d §96) are unchanged — parameterized calls work inside action blocks.
- `choose` (v2d §99) is unchanged — legal inside action blocks, side-effect-only.
- Generalized `of` (v2b §77) is unchanged — works in `when`/`unless` conditions via `choose`-style resolution.
- Quoting (v2c §85–§92) is unchanged — quoted strings work in action blocks and conditions.
- The five-outcome taxonomy (v1c §50) is extended by `error_runtime` for listener mode.
- Stepwise execution (v1d §56) applies within action blocks.

---

## RESUME PROMPT (Inscript Programming Language v3a)

*We are resuming from the Inscript Programming Language Event-Driven Execution Addendum v3a (May 12, 2026), which extends v2d Composition Parameters and Conditional Branching (May 12, 2026), and back through v2c/v2b/v2a/v1d/v1c/v1b/v1a and the Inception Checkpoint v1 (all May 11–12, 2026). v3a resolves Q13 (event-driven execution) and closes Branch F. The execution model transitions from sequential-only to two-phase: Phase 1 runs all statements sequentially (v2d-identical); Phase 2 enters listener mode if handlers exist and Phase 1 had zero errors. **Core architecture:** `when` registers reactive handlers with `choose`-style value-expression conditions (symbol table names, `of` expressions); `unless` is a guard clause (compound eligibility = when-true AND unless-false, edge-triggered on compound state); `finish` exits listener mode immediately and totally (no further statements, cascades, handlers, or updates). **Action blocks** use indentation (min one space, tabs rejected, block ends at unindented line). All v2d verbs + `finish` legal inside action blocks; `remember`/`filter` on live adapter values prohibited inside action blocks (Phase 2 ownership); Phase 1 `remember` may initialize live values. **Event sources:** domain pack adapter contract (declaration with name+type, adapter enqueues `(name, value)` pairs, lifecycle start/stop). Single-threaded event queue — one update processed to completion before next dequeue. **Evaluation:** edge-triggered with deep value equality; unset live values = false; unchanged updates = no re-evaluation; modifications coalesced by name after action block completion. **Cascading:** depth-first, conservative cycle detection (same handler twice in one chain = error), non-fatal errors don't suppress cascades. **Execution ordering:** registration order, complete-turn semantics. **Initial evaluation:** before adapter dispatch, registration order, same semantics as event processing; `finish` during initial evaluation prevents adapter start; no adapters = auto-shutdown after initial evaluation. **Result interface:** four new statuses (listening, handler_fire, shutdown, error_runtime); trigger metadata with source/values_changed/new_values; shutdown metadata with reason. **Vocabulary:** 10 verbs, 14 connectives, 34 reserved words (was 9/12/33 in v2d). Eighteen new test sentences (96–113). Build specification is now ten documents: inception checkpoint v1, addenda v1a/v1b/v1c/v1d/v2a/v2b/v2c/v2d/v3a, plus the 113-sentence test suite. `transform`/`compare` remain deferred. Tile interface, domain packs as product surfaces, and domain pack activation syntax are not built. The sequential feature set (v2d) and the reactive feature set (v3a) together form a structurally complete programming language.*

---

## PROVENANCE NOTE

This addendum was verified against:

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026):
  - §10 (concept-layer vocabulary) — `when`, `unless`, and `finish` are concept-layer words. `when` names what the user wants (react to a condition). `unless` names an exception. `finish` names an intention (stop).
  - §11 (vocabulary table, v2 deferred tier) — `when` and `unless` were deferred temporal connectives. Now activated.
  - §13 (v1/v2 use-case split) — healthcare monitoring, smart home, and reactive game logic were v2 (event-driven). This addendum provides the execution model they require.
  - §16 (pipeline architecture) — unchanged. The lexer → reorderer → parser → analyzer → interpreter pipeline applies to both phases.
  - §17 (verb signatures, slot filling) — `finish` has no slots (no target, no condition). `when` signature: condition + optional guard + action block.
  - §25 (Q13, event-driven execution) — resolved by this addendum.
- **`inscript_addendum_v1a_pre_build.md`** (May 11, 2026):
  - §30 (amber precedence) — applied to `when`/`unless` at registration time (§123).
- **`inscript_addendum_v1c_implementation_hardening.md`** (May 11, 2026):
  - §48 (blank lines skipped) — applies inside action blocks (§110).
  - §50 (five-outcome taxonomy) — extended by `error_runtime` for listener mode (§122).
  - §52 (deterministic interpretation) — the single-threaded event queue (§119) and deep value equality (§113) preserve deterministic interpretation in listener mode.
- **`inscript_addendum_v1d_build_boundary.md`** (May 11, 2026):
  - §56 (stepwise execution) — applies within action blocks (§111).
  - §64 (structured result objects) — extended with listener-specific result types (§122).
- **`inscript_addendum_v2a_dogfooding_resolutions.md`** (May 12, 2026):
  - §67 (`keep` verb) — `keep` on live values is legal (non-destructive). `filter` on live values is not (destructive).
- **`inscript_addendum_v2b_composition_returns.md`** (May 12, 2026):
  - §76 (composition return values, side-effect-only list) — extended with `finish` and `when` (both side-effect-only).
  - §77 (generalized `of`) — `of` expressions work in `when`/`unless` conditions via `choose`-style resolution (§108).
- **`inscript_addendum_v2c_multi_word_strings.md`** (May 12, 2026):
  - §85–§92 (quoting mechanism) — quoted strings work in action blocks and `when`/`unless` conditions via existing value-position rules.
- **`inscript_addendum_v2d_parameters_and_branching.md`** (May 12, 2026):
  - §96–§98 (composition parameters) — parameterized calls work inside action blocks (§111). `from` disambiguation table unchanged — the five v2d entries apply.
  - §99–§102 (`choose` verb) — legal inside action blocks (§111). `choose` is side-effect-only; `choose` inside `each` remains deferred.
  - §103 (`transform`/`compare` deferral) — unchanged.
  - §104 (vocabulary) — extended in §124.
  - §105 (test sentences 81–95) — extended in §125 (96–113).
  - §106 (build boundary) — extended in §126.
- **External review** (ChatGPT, May 12, 2026): 60 findings across version drift, architectural gaps, and clarification needs. The version drift (findings 1–4, 26, 38, 58–60) was resolved by rebasing on v2d. Twelve architectural decisions were approved by the architect. The remaining clarification-level findings were resolved using existing locked principles. All 60 findings are addressed in this addendum.
- **Internal consistency verification** (May 12, 2026): This addendum was checked for the failure mode identified during the inception checkpoint session (May 11, 2026): claiming a use case is achievable without verifying the architecture supports it. Each of the three v2 use cases (healthcare, smart home, game design) was traced through the full v3a architecture: domain pack declares live values → values visible during Phase 1 → `when` handler registered with registration-time validation → Phase 2 starts after zero-error Phase 1 → initial evaluation → adapters dispatch → single-threaded event queue → edge-triggered evaluation → handler fires with complete-turn semantics → cascades resolve → next update dequeued. All three use cases require only the mechanisms specified here plus a domain-pack adapter for their respective external systems.
- **Filename:** `inscript_addendum_v3a_event_driven_execution.md` — domain `inscript` (provisional, pre-vault), class `addendum`, version `v3a` (first addendum in the v3 series, marking the transition from sequential to event-driven execution), subtitle `event_driven_execution`.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE EVENT-DRIVEN EXECUTION ADDENDUM v3a*

*May 12, 2026*

*The inception checkpoint asked: "How does the interpreter transition from 'run and finish' to 'listen and react'?"*
*The answer: it doesn't transition. It does both. Phase 1 runs. Phase 2 listens. The program decides which mode it needs by whether it contains `when` blocks.*
*Sixty review findings. Twelve architect decisions. Zero unaddressed.*
*The vocabulary grows by one word. The architecture grows by one phase. The user writes prose either way.*

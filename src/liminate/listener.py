"""Phase 2 listener (event-driven runtime) for Liminate v3a.

Sources:
- v3a §107 (two-phase execution; Phase 2 gated on zero Phase 1 errors)
- v3a §113 (edge-triggered evaluation; deep value equality; unset = false;
  unchanged updates produce no re-evaluation; modifications coalesced
  by name after the action block completes)
- v3a §114 (cascading triggers; depth-first; conservative cycle detection
  — same handler firing twice in one chain is a runtime error)
- v3a §115 (registration-order firing with complete-turn semantics)
- v3a §117 (live-value lifecycle: unset → active → inactive)
- v3a §119 (single-threaded event queue; one update to completion before
  next dequeue)
- v3a §120 (adapter failure isolation; dependent handlers disable)
- v3a §121 (initial evaluation before adapter dispatch)
- v3a §122 (result interface: LISTENING, HANDLER_FIRE, SHUTDOWN,
  ERROR_RUNTIME — trigger envelope and shutdown reason metadata)

This module's `listen()` is a Python generator that yields structured
results in order: a LISTENING marker, zero or more HANDLER_FIRE /
ERROR_SEMANTIC / ERROR_RUNTIME results, and a terminal SHUTDOWN. The
CLI display loop streams these to stdout; integration tests drain
them into a list and assert on shape.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from queue import Empty, Queue
from typing import Any, Iterator

from .adapter import (
    Adapter,
    AdapterDone,
    AdapterFailure,
    AdapterUpdate,
    LiveValueRegistry,
)
from .analyzer import SymbolEntry, analyze
from .interpreter import (
    HandlerTable,
    _exec_op,
    _FinishRequested,
    _RequirementNotMet,
    _RuntimeError,
    _in_action_block,
    _live_value_names_ctx,
    decay_tick,
)
from .vocabulary import DecayingValue
from .parser import (
    ASTNode,
    CompoundConditionNode,
    ConditionNode,
    FieldAccessNode,
    FinishNode,
    NameRef,
    SequenceNode,
    WhenNode,
)
from .renderer import render
from .result import LiminateResult, ResultStatus


# How long to block on queue.get when adapters might still push. Short
# enough that finishing tests don't drag, long enough not to busy-wait.
_QUEUE_POLL_SECONDS = 0.05


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def listen(
    symtab: dict[str, SymbolEntry],
    handler_table: HandlerTable,
    live_value_registry: LiveValueRegistry,
    adapters: list[Adapter],
) -> Iterator[LiminateResult]:
    """Run Phase 2 — the event-driven listener (§107 startup sequence).

    Yields, in order:
      1. One LISTENING marker (always).
      2. HANDLER_FIRE results from initial evaluation (§121).
      3. HANDLER_FIRE / ERROR_SEMANTIC / ERROR_RUNTIME from each adapter
         update + cascades (§115/§119/§114).
      4. One terminal SHUTDOWN result.

    The generator returns after yielding SHUTDOWN; callers must not
    consume further. Callers may stop iteration early — adapters will be
    stopped on the next yield attempt via their `stop()` methods (the
    runner stops them defensively before yielding SHUTDOWN as well).
    """
    runner = _Runner(symtab, handler_table, live_value_registry, adapters)
    yield from runner.run()


# ---------------------------------------------------------------------------
# Internal runner — collects all v3a §107–§122 state in one place
# ---------------------------------------------------------------------------


@dataclass
class _Runner:
    symtab: dict[str, SymbolEntry]
    handler_table: HandlerTable
    live_value_registry: LiveValueRegistry
    adapters: list[Adapter]
    queue: Queue = field(default_factory=Queue)
    finish_requested: bool = False
    finish_handler_index: int | None = None

    def run(self) -> Iterator[LiminateResult]:
        # §122 — listener entry marker. Watching names come from the
        # union of all handler dependencies; ordering is deterministic
        # (handler_table.watching_names).
        yield LiminateResult(
            status=ResultStatus.LISTENING,
            metadata={"watching": self.handler_table.watching_names()},
        )

        # §121 — initial evaluation runs before adapters start. `finish`
        # during initial evaluation prevents adapters from ever starting.
        yield from self._initial_evaluation()
        if self.finish_requested:
            yield self._shutdown_finish()
            return

        # §107 — no adapters means auto-shutdown after initial evaluation.
        if not self.adapters:
            yield self._shutdown_no_adapters()
            return

        # §120 — start adapters. The interpreter never reads from the
        # queue itself; adapters push their entire (scripted) script in
        # `start()`. Real adapters would push on background threads.
        for adapter in self.adapters:
            adapter.attach_queue(self.queue)
            adapter.start()

        # §119 — drain the queue. One update at a time, to completion.
        active_adapters = {a.name for a in self.adapters}
        while active_adapters:
            try:
                msg = self.queue.get(timeout=_QUEUE_POLL_SECONDS)
            except Empty:
                # Idle poll — no message arrived this quantum. Loop and
                # keep waiting. Real adapters with intervals longer than
                # _QUEUE_POLL_SECONDS will see many of these between
                # updates; that's fine. The loop only exits when every
                # adapter has signaled AdapterDone (or AdapterFailure),
                # at which point `active_adapters` becomes empty and the
                # `while` condition terminates the loop naturally.
                continue
            if isinstance(msg, AdapterDone):
                active_adapters.discard(msg.adapter_name)
                continue
            if isinstance(msg, AdapterFailure):
                yield from self._handle_adapter_failure(msg)
                active_adapters.discard(msg.adapter_name)
                continue
            if isinstance(msg, AdapterUpdate):
                yield from self._handle_adapter_update(msg)
                if self.finish_requested:
                    yield self._shutdown_finish()
                    return
                continue
            # Unknown message — log and continue (defensive; the queue
            # shape is fully under our control).

        # §120 — terminal shutdown. Either all adapters signaled Done,
        # or the queue drained and we timed out waiting for more.
        for adapter in self.adapters:
            adapter.stop()
        yield self._shutdown_adapter_complete()

    # -------------------------------------------------------------------
    # Metabolic Era batch 1 — decay tick driver
    # -------------------------------------------------------------------

    def tick_decay(self) -> Iterator[LiminateResult]:
        """Advance every DecayingValue entry by one tick, then fire any
        handlers whose compound eligibility transitioned false → true.

        Treats every decaying name as `modified` for the cascade so that
        handlers watching those names are re-evaluated on edge.
        """
        decaying = [
            name for name, e in self.symtab.items()
            if isinstance(e.value, DecayingValue)
        ]
        if not decaying:
            return
        decay_tick(self.symtab)
        new_values = {
            n: self.symtab[n].value.current_value for n in decaying
        }
        yield from self._fire_eligible(
            modified_names=decaying,
            new_values=new_values,
            source="decay_tick",
            cascade_chain=frozenset(),
        )

    # -------------------------------------------------------------------
    # Initial evaluation (§121)
    # -------------------------------------------------------------------

    def _initial_evaluation(self) -> Iterator[LiminateResult]:
        """Evaluate every registered handler in registration order. Fire
        the ones whose compound eligibility is true (§115 complete-turn
        semantics). Updates `last_eligibility` for every handler so the
        event loop's edge-triggered comparison starts from the right
        baseline."""
        for handler in list(self.handler_table.handlers):
            if handler.disabled:
                handler.last_eligibility = False
                continue
            elig = self._eligibility(handler)
            handler.last_eligibility = elig
            if not elig:
                continue
            yield from self._fire_handler(
                handler,
                source="initial",
                values_changed=[],
                new_values={},
                cascade_chain=frozenset({handler.index}),
            )
            if self.finish_requested:
                return

    # -------------------------------------------------------------------
    # Adapter update handling (§113, §115, §119)
    # -------------------------------------------------------------------

    def _handle_adapter_update(
        self, update: AdapterUpdate,
    ) -> Iterator[LiminateResult]:
        """One update is processed to completion before the next dequeue.

        §113 — change detection uses deep Liminate value equality.
        Equal new value: silent absorb. Different (or unset → any):
        write to symbol table, mark live value active, re-evaluate
        handlers that depend on this name, fire any false→true
        transitions in registration order (§115).
        """
        name, new_value = update.name, update.value
        entry = self.symtab.get(name)
        old_value = entry.value if entry is not None else None
        was_unset = self.live_value_registry.is_unset(name)

        # §113: if the new value equals the stored one (and the live
        # value is already active), it's a no-op.
        if not was_unset and _values_equal(old_value, new_value):
            return

        # Write the value, infer/preserve the entry's metadata. We avoid
        # the interpreter's _store helper because that would re-infer
        # types and source_names — for live values we want to preserve
        # the pack-declared type while updating the runtime value.
        if entry is None:
            entry = SymbolEntry(
                name=name, value=copy.deepcopy(new_value), type="unknown",
            )
            self.symtab[name] = entry
        else:
            entry.value = copy.deepcopy(new_value)
        self.live_value_registry.mark_active(name)

        # Fire handlers (depth-first cascading inside _fire_eligible).
        yield from self._fire_eligible(
            modified_names=[name],
            new_values={name: new_value},
            source="adapter_update",
            cascade_chain=frozenset(),
        )

    # -------------------------------------------------------------------
    # Eligibility, firing, cascade (§113, §114, §115)
    # -------------------------------------------------------------------

    def _fire_eligible(
        self,
        modified_names: list[str],
        new_values: dict[str, Any],
        source: str,
        cascade_chain: frozenset[int],
    ) -> Iterator[LiminateResult]:
        """For each handler dependent on `modified_names`, evaluate the
        compound eligibility. If a handler transitioned false→true,
        fire it (§113). Handlers fire in registration order (§115)."""
        # Collect handlers whose dependency set intersects the modified
        # names, dedupe, sort by registration index.
        candidates: dict[int, Any] = {}
        for name in modified_names:
            for handler in self.handler_table.dependents_of(name):
                candidates[handler.index] = handler
        ordered = [candidates[i] for i in sorted(candidates.keys())]

        for handler in ordered:
            if handler.disabled:
                continue
            new_elig = self._eligibility(handler)
            old_elig = handler.last_eligibility
            handler.last_eligibility = new_elig
            if not new_elig or old_elig:
                # Not eligible, or already true (no edge) → don't fire.
                continue
            if handler.index in cascade_chain:
                # §114 — same handler firing twice in one chain is a
                # conservative cycle. Don't fire; emit an ERROR_RUNTIME
                # describing the path. The handler stays active for
                # future events.
                yield self._cycle_error(handler, cascade_chain)
                continue
            new_chain = cascade_chain | {handler.index}
            yield from self._fire_handler(
                handler,
                source=source,
                values_changed=list(modified_names),
                new_values=dict(new_values),
                cascade_chain=new_chain,
            )
            if self.finish_requested:
                return

    def _fire_handler(
        self,
        handler: Any,  # Handler — late binding to avoid circular import
        source: str,
        values_changed: list[str],
        new_values: dict[str, Any],
        cascade_chain: frozenset[int],
    ) -> Iterator[LiminateResult]:
        """Execute a handler's action block. Yields one result per
        statement (HANDLER_FIRE on success, ERROR_SEMANTIC on action-
        statement failure — both wrapped with §122 trigger metadata).
        After completion, cascade resolution fires dependent handlers
        depth-first (§114)."""
        # Snapshot watched-name values so we can detect what was
        # modified by this action block (§113 — modifications coalesced
        # by name after the action block completes).
        watched_names = self.handler_table.watching_names()
        pre_snapshot = {
            n: _snapshot_value(self.symtab.get(n)) for n in watched_names
        }

        action = handler.when_node.action
        statements = (
            list(action.operations)
            if isinstance(action, SequenceNode)
            else [action]
        )

        # Set the interpreter's action-block context for the duration
        # of this handler's firing. _exec_composition_call and the
        # nested-SequenceNode dispatch in _exec_op read these vars when
        # re-analyzing inner ops for stepwise semantics (v1d §56).
        tok_in_action = _in_action_block.set(True)
        tok_live_names = _live_value_names_ctx.set(
            self.live_value_registry.names(),
        )
        try:
            yield from self._fire_handler_body(
                handler, source, values_changed, new_values,
                cascade_chain, statements, pre_snapshot, watched_names,
            )
        finally:
            _in_action_block.reset(tok_in_action)
            _live_value_names_ctx.reset(tok_live_names)

    def _fire_handler_body(
        self,
        handler: Any,
        source: str,
        values_changed: list[str],
        new_values: dict[str, Any],
        cascade_chain: frozenset[int],
        statements: list[ASTNode],
        pre_snapshot: dict[str, Any],
        watched_names: list[str],
    ) -> Iterator[LiminateResult]:
        for stmt in statements:
            # Analyze each action statement at firing time with full
            # context (live-value names + in_action_block=True). Name
            # resolution that was deferred at registration runs now.
            analysis = analyze(
                stmt, self.symtab,
                in_action_block=True,
                live_value_names=self.live_value_registry.names(),
            )
            if isinstance(analysis, LiminateResult):
                if analysis.canonical is None:
                    try:
                        analysis.canonical = render(stmt)
                    except Exception:
                        pass
                yield self._wrap_with_trigger(
                    analysis, source, handler, values_changed, new_values,
                )
                continue

            # Execute the statement. _exec_op raises _FinishRequested
            # when a `finish` is reached anywhere in the statement's
            # evaluation (top-level FinishNode, inside a choose branch,
            # inside a composition body) — §112 immediate-and-total
            # semantics. We catch it here, mark the listener for
            # shutdown, and return without yielding a result for this
            # statement (§112 — `finish yields only the shutdown
            # result`).
            try:
                output = _exec_op(stmt, self.symtab)
            except _FinishRequested:
                self.finish_requested = True
                self.finish_handler_index = handler.index
                return  # no further statements, no cascades
            except _RuntimeError as e:
                yield self._wrap_with_trigger(
                    LiminateResult(
                        status=ResultStatus.ERROR_SEMANTIC,
                        canonical=render(stmt),
                        message=e.message,
                        executed=False,
                    ),
                    source, handler, values_changed, new_values,
                )
                continue
            except _RequirementNotMet as e:
                # Normative Era batch 2 — a `require` inside an action
                # block failed. Report the failure on this statement and
                # continue with the rest of the block (handlers shouldn't
                # bring down the whole listener over one failed rule).
                yield self._wrap_with_trigger(
                    LiminateResult(
                        status=ResultStatus.REQUIREMENT_NOT_MET,
                        canonical=render(stmt),
                        message=e.message,
                        executed=False,
                    ),
                    source, handler, values_changed, new_values,
                )
                continue

            # §122 — successful action statements are HANDLER_FIRE.
            yield self._wrap_with_trigger(
                LiminateResult(
                    status=ResultStatus.HANDLER_FIRE,
                    canonical=render(stmt),
                    output=output if output else None,
                    executed=True,
                ),
                source, handler, values_changed, new_values,
            )

        if self.finish_requested:
            return

        # §113 — collect names whose value changed during execution.
        # Coalesced by name (intermediate values inside `each` etc. do
        # not generate separate cascade triggers).
        modified: list[str] = []
        modified_values: dict[str, Any] = {}
        for n in watched_names:
            cur_entry = self.symtab.get(n)
            cur_value = cur_entry.value if cur_entry is not None else None
            if not _values_equal(pre_snapshot.get(n), cur_value):
                modified.append(n)
                modified_values[n] = cur_value

        if not modified:
            return

        # §114 — depth-first cascade with cycle guarding via cascade_chain.
        yield from self._fire_eligible(
            modified_names=modified,
            new_values=modified_values,
            source="cascade",
            cascade_chain=cascade_chain,
        )

    # -------------------------------------------------------------------
    # Eligibility evaluation (§113)
    # -------------------------------------------------------------------

    def _eligibility(self, handler: Any) -> bool:
        """Compute compound eligibility: when-condition AND NOT
        unless-guard (§109). Unset live values make the condition false
        (§113)."""
        cond = self._eval_condition(handler.when_node.condition)
        if not cond:
            return False
        if handler.when_node.unless is None:
            return True
        guard = self._eval_condition(handler.when_node.unless)
        return cond and not guard

    def _eval_condition(self, cond: ASTNode) -> bool:
        if isinstance(cond, CompoundConditionNode):
            l = self._eval_condition(cond.left)
            if cond.connector == "and":
                return l and self._eval_condition(cond.right)
            return l or self._eval_condition(cond.right)
        if isinstance(cond, ConditionNode):
            left = self._eval_operand(cond.field)
            right = self._eval_operand(cond.value)
            if left is _UNSET or right is _UNSET:
                return False
            if cond.op == "within":
                # Issue #19: |field - target| <= tolerance. `value` is the
                # tolerance, `value2` the target.
                target = self._eval_operand(cond.value2)
                if target is _UNSET:
                    return False
                if any(
                    isinstance(v, bool) or not isinstance(v, (int, float))
                    for v in (left, right, target)
                ):
                    return False
                return abs(left - target) <= right
            return _apply_op(cond.op, left, right)
        return False

    def _eval_operand(self, node: ASTNode) -> Any:
        """Resolve a `when`/`unless` operand against the current symbol
        table. Returns the sentinel `_UNSET` when the operand refers to
        an unset live value (§113)."""
        from .parser import (
            BareWord, NumberLiteral, QuotedString,
        )
        if isinstance(node, NumberLiteral):
            return node.value
        if isinstance(node, QuotedString):
            return node.content
        if isinstance(node, BareWord):
            entry = self.symtab.get(node.word)
            if entry is None:
                return node.word  # bare word literal fallback
            if self.live_value_registry.is_unset(node.word):
                return _UNSET
            val = entry.value
            if isinstance(val, DecayingValue):
                return val.current_value
            return val
        if isinstance(node, NameRef):
            entry = self.symtab.get(node.name)
            if entry is None:
                # Registration-time validation should have caught this;
                # treat as unset for defensive runtime safety.
                return _UNSET
            if self.live_value_registry.is_unset(node.name):
                return _UNSET
            val = entry.value
            if isinstance(val, DecayingValue):
                return val.current_value
            return val
        if isinstance(node, FieldAccessNode):
            entry = self.symtab.get(node.record_name)
            if entry is None:
                return _UNSET
            if self.live_value_registry.is_unset(node.record_name):
                return _UNSET
            record = entry.value
            if not isinstance(record, dict) or node.field not in record:
                return _UNSET
            return record[node.field]
        return _UNSET

    # -------------------------------------------------------------------
    # Wrapping / metadata helpers
    # -------------------------------------------------------------------

    def _wrap_with_trigger(
        self,
        base: LiminateResult,
        source: str,
        handler: Any,
        values_changed: list[str],
        new_values: dict[str, Any],
    ) -> LiminateResult:
        """v3a §122 — attach the trigger envelope to an action-statement
        result. Successful results were already created with
        HANDLER_FIRE status; error results keep their original status."""
        base.metadata = {
            "trigger": {
                "source": source,
                "handler_index": handler.index,
                "values_changed": list(values_changed),
                "new_values": dict(new_values),
            },
        }
        return base

    def _cycle_error(
        self,
        handler: Any,
        cascade_chain: frozenset[int],
    ) -> LiminateResult:
        """v3a §114: produce ERROR_RUNTIME with the traced chain. The
        chain is sorted by handler index for stable presentation."""
        path = sorted(cascade_chain) + [handler.index]
        return LiminateResult(
            status=ResultStatus.ERROR_RUNTIME,
            message=(
                f"Cycle detected — handler {handler.index} would fire "
                f"a second time in the same cascade chain "
                f"(path: {path})."
            ),
            metadata={
                "kind": "cycle",
                "handler_index": handler.index,
                "path": path,
            },
        )

    def _handle_adapter_failure(
        self, msg: AdapterFailure,
    ) -> Iterator[LiminateResult]:
        """v3a §120: isolate the failed adapter. Mark its live values
        inactive; disable any handler whose dependencies are now all
        inactive."""
        yield LiminateResult(
            status=ResultStatus.ERROR_RUNTIME,
            message=(
                f"Adapter '{msg.adapter_name}' failed: {msg.reason}"
            ),
            metadata={
                "kind": "adapter_failure",
                "adapter": msg.adapter_name,
                "reason": msg.reason,
            },
        )
        affected = self.live_value_registry.mark_inactive_for_adapter(
            msg.adapter_name,
        )
        if not affected:
            return
        affected_set = set(affected)
        for handler in self.handler_table.handlers:
            if handler.disabled:
                continue
            # If every name this handler depends on is now inactive (or
            # was already inactive), the handler is dead. Conservatively
            # we only disable when ALL deps are gone — partial coverage
            # means the handler can still fire on the remaining names.
            inactive_names = (
                set(self.live_value_registry.names())
                - self.live_value_registry.active_names()
            )
            non_inactive_deps = handler.dependencies - inactive_names
            if not non_inactive_deps and (handler.dependencies & affected_set):
                handler.disabled = True

    # -------------------------------------------------------------------
    # Shutdown builders (§122)
    # -------------------------------------------------------------------

    def _shutdown_finish(self) -> LiminateResult:
        for adapter in self.adapters:
            adapter.stop()
        meta: dict[str, Any] = {"reason": "finish"}
        if self.finish_handler_index is not None:
            meta["handler_index"] = self.finish_handler_index
        return LiminateResult(
            status=ResultStatus.SHUTDOWN,
            output=["Listener stopped: finish called."],
            metadata=meta,
        )

    def _shutdown_adapter_complete(self) -> LiminateResult:
        return LiminateResult(
            status=ResultStatus.SHUTDOWN,
            output=["Listener stopped: all event sources completed."],
            metadata={"reason": "adapter_complete"},
        )

    def _shutdown_no_adapters(self) -> LiminateResult:
        return LiminateResult(
            status=ResultStatus.SHUTDOWN,
            output=["Listener stopped: no event sources registered."],
            metadata={"reason": "no_adapters"},
        )


# ---------------------------------------------------------------------------
# Value equality + small helpers (v3a §113)
# ---------------------------------------------------------------------------


class _Unset:
    """Sentinel marking an unset live-value operand during eligibility
    evaluation. Comparisons involving `_UNSET` return False (§113)."""
    __slots__ = ()

    def __repr__(self) -> str:
        return "<unset>"


_UNSET = _Unset()


def _values_equal(a: Any, b: Any) -> bool:
    """Liminate deep value equality (v3a §113): numbers/strings are
    scalar-equal; lists are deep-equal element-wise; records are
    deep-equal by fields. Note: this is not Python identity, and `True`
    vs `1` are distinguished only by type (Liminate has no booleans —
    `True` shouldn't appear in user values)."""
    if type(a) is not type(b):
        # Numbers and booleans share `==` semantics; we keep that.
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a == b
        return False
    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(_values_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_values_equal(a[k], b[k]) for k in a)
    return a == b


def _snapshot_value(entry: SymbolEntry | None) -> Any:
    """Deep-copy a symbol entry's value for snapshot comparison.
    `None`/missing entries snapshot as None."""
    if entry is None:
        return None
    return copy.deepcopy(entry.value)


def _apply_op(op: str, a: Any, b: Any) -> bool:
    """Operator dispatch shared with the sequential interpreter. Keeping
    a copy here avoids the circular import between interpreter and
    listener modules.

    NOTE: this function is duplicated in interpreter.py. Both copies
    must stay in sync when adding new operators.
    """
    if op == "is":
        return a == b
    if op == "above":
        return a > b
    if op == "below":
        return a < b
    if op == "equal_to":
        return a == b
    if op == "not_above":
        return not (a > b)
    if op == "not_below":
        return not (a < b)
    if op == "not_equal_to":
        return a != b
    if op == "includes":
        if isinstance(a, list):
            return b in a
        return False
    if op == "not_includes":
        if isinstance(a, list):
            return b not in a
        return True
    raise ValueError(f"Unknown comparison operator '{op}'.")

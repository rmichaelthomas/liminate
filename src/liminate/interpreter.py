"""Interpreter for Liminate v1 / v2a / v2b / v2c / v2d / v3a.

Sources:
- inception §24 (interpreter behaviors: auto-show, in-place filter,
  inline gather naming, copy semantics)
- v1b §38 (combine is numeric sum)
- v1b §39 (combine is non-destructive)
- v1b §40 (gather stores AND auto-shows)
- v1b §41 (named composition call executes stored body)
- v1b §42 (display formats)
- v1c §49 (iterator context — temporary binding for each)
- v1c §50 (five outcomes; this module produces SUCCESS or
  ERROR_SEMANTIC outcomes — parse/amber outcomes come from earlier
  pipeline stages)
- v1c §52 (deterministic interpretation only)
- v1d §56 (stepwise execution — multi-op sequences commit independently)
- v1d §57 (lowercased identifiers and string values)
- v1d §58 (duplicate names overwrite silently)
- v1d §64 (structured result objects; no direct I/O)
- v3a §108 (Phase 1 `when` registration into a handler table; no
  action-block execution at this stage)
- v3a §117 (Phase 1 `remember` of a declared live value transitions
  the registry entry from "unset" to "active")

This module performs both the per-op analyze gate and execution. The
analyzer is re-invoked per operation inside SequenceNode bodies and
composition bodies so that mid-sequence failures honor stepwise
semantics (v1d §56).
"""

from __future__ import annotations

import copy
import re
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from .adapter import LiveValueRegistry
from .analyzer import SymbolEntry, analyze
from .vocabulary import (
    AppendToListExecution,
    CompareValuesExecution,
    DecayingValue,
    NumericExtractCompareExecution,
    SetFieldExecution,
    SetValueExecution,
    SubstringCheckExecution,
    get_pack_verb_owner,
)


# v3a — the interpreter's re-analyses inside _exec_composition_call and
# _execute_sequence need to know whether the current execution is
# happening inside a `when` action block. The listener sets these
# context vars before driving _exec_op; everywhere else they default
# to False/None (Phase 1 sequential behavior).
_in_action_block: ContextVar[bool] = ContextVar(
    "liminate_in_action_block", default=False,
)
_live_value_names_ctx: ContextVar[set[str] | None] = ContextVar(
    "liminate_live_value_names", default=None,
)
from .parser import (
    AddNode,
    ArithmeticNode,
    AssignNode,
    ASTNode,
    BareWord,
    ChooseBranch,
    ChooseNode,
    CombineNode,
    CompareNode,
    CompositionCallNode,
    CompoundConditionNode,
    ConditionNode,
    CountNode,
    EachNode,
    EachPronoun,
    ExpectNode,
    FieldAccessNode,
    FilterNode,
    FinishNode,
    GatherNode,
    KeepNode,
    NameRef,
    NumberLiteral,
    PackVerbNode,
    QuotedString,
    RemoveNode,
    RememberCompositionNode,
    RememberListNode,
    RememberRecordNode,
    RememberValueNode,
    RequireNode,
    RequireEachNode,
    ForbidNode,
    PermitNode,
    SequenceNode,
    ShowNode,
    SortNode,
    TransformNode,
    WeakensNode,
    WhenNode,
)
from .renderer import render
from .result import LiminateResult, ResultStatus


# ---------------------------------------------------------------------------
# Handler table (v3a §108) — registration-time state for `when` blocks
# ---------------------------------------------------------------------------


@dataclass
class Handler:
    """A `when` handler registered during Phase 1 (v3a §108).

    `index` is the registration order, surfaced in trigger metadata as
    `handler_index` (§122). `dependencies` is the set of symbol names
    referenced by the condition and (optional) unless guard — per §108
    "dependency extraction rule", `<field> of <record>` depends on the
    record, not the field. `last_eligibility` tracks the most-recent
    compound-eligibility value so the event loop (Phase 9) can detect
    false→true transitions (§113 edge triggering). `disabled` is set
    when a depended-on adapter has failed (§120) — disabled handlers
    are skipped during event processing.
    """
    index: int
    when_node: WhenNode
    dependencies: frozenset[str]
    # Source-order, deduped name walk of (condition, unless). Preserves
    # the order the user wrote so the LISTENING marker reports watching
    # names in a reading order matching the program. `dependencies` (the
    # frozenset) is kept for fast `in` lookups and set algebra in §120
    # adapter-failure handling.
    dependency_order: tuple[str, ...] = ()
    last_eligibility: bool = False
    disabled: bool = False


@dataclass
class HandlerTable:
    """Ordered list of registered `when` handlers (v3a §108/§115).

    Registration order is the firing order for ties (v3a §115 — multiple
    handlers eligible from the same update fire in registration order).
    """
    handlers: list[Handler] = field(default_factory=list)

    def register(self, when_node: WhenNode) -> Handler:
        ordered = _extract_when_dependency_order(when_node)
        handler = Handler(
            index=len(self.handlers),
            when_node=when_node,
            dependencies=frozenset(ordered),
            dependency_order=ordered,
        )
        self.handlers.append(handler)
        return handler

    def watching_names(self) -> list[str]:
        """Union of all dependency names across all handlers, in
        registration order. Within a single handler, names appear in
        source-walk order (condition first, then unless guard). Across
        handlers, first-seen wins. Surfaced in the LISTENING marker
        (§122)."""
        seen: set[str] = set()
        result: list[str] = []
        for h in self.handlers:
            for name in h.dependency_order:
                if name not in seen:
                    seen.add(name)
                    result.append(name)
        return result

    def dependents_of(self, name: str) -> list[Handler]:
        """Active (non-disabled) handlers that reference `name` in
        their condition or guard. Order preserves registration order
        for §115 ordering."""
        return [
            h for h in self.handlers
            if name in h.dependencies and not h.disabled
        ]

    def is_empty(self) -> bool:
        return not self.handlers


def _extract_when_dependencies(when_node: WhenNode) -> frozenset[str]:
    """Walk the `when` condition and `unless` guard, collecting the
    symbol names a handler depends on (v3a §108 dependency rule).

    - Bare names (NameRef) depend on themselves.
    - `<field> of <record>` depends on the record name only — handlers
      re-evaluate when the record value changes.
    - Literals (NumberLiteral, BareWord, QuotedString) contribute no
      dependencies. Note: a BareWord that happens to match a symbol-
      table name still resolves at evaluation time; we conservatively
      do not register it here because §108 says conditions resolve to
      a comparison between values, not lookups during dependency
      extraction.
    """
    return frozenset(_extract_when_dependency_order(when_node))


def _extract_when_dependency_order(when_node: WhenNode) -> tuple[str, ...]:
    """Like `_extract_when_dependencies` but preserves first-encounter
    order across a left-to-right walk of (condition, unless). Used by
    `HandlerTable.watching_names` (§122) so the LISTENING marker
    reports names in the order the user wrote them."""
    seen: set[str] = set()
    ordered: list[str] = []
    _walk_dependencies(when_node.condition, seen, ordered)
    if when_node.unless is not None:
        _walk_dependencies(when_node.unless, seen, ordered)
    return tuple(ordered)


def _walk_dependencies(
    node: ASTNode, seen: set[str], ordered: list[str],
) -> None:
    if isinstance(node, ConditionNode):
        _walk_dependencies(node.field, seen, ordered)
        _walk_dependencies(node.value, seen, ordered)
        # Issue #19: the `within` target operand is also a dependency, so a
        # Phase 2 `when` handler watches the target variable for changes.
        if node.value2 is not None:
            _walk_dependencies(node.value2, seen, ordered)
    elif isinstance(node, CompoundConditionNode):
        _walk_dependencies(node.left, seen, ordered)
        _walk_dependencies(node.right, seen, ordered)
    elif isinstance(node, NameRef):
        if node.name not in seen:
            seen.add(node.name)
            ordered.append(node.name)
    elif isinstance(node, FieldAccessNode):
        if node.record_name not in seen:
            seen.add(node.record_name)
            ordered.append(node.record_name)
    # Literals (NumberLiteral, BareWord, QuotedString, EachPronoun)
    # contribute no dependencies — they evaluate to themselves.


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def execute(
    ast: ASTNode,
    symbol_table: dict[str, SymbolEntry],
    *,
    handler_table: HandlerTable | None = None,
    live_value_registry: LiveValueRegistry | None = None,
) -> LiminateResult:
    """Execute a single top-level AST against a mutable symbol table.

    Returns an LiminateResult. For SequenceNode the interpreter loops
    per-op so that earlier successes commit even if a later op fails
    (v1d §56).

    v3a parameters:
    - `handler_table`: when set, WhenNode statements register here
      rather than raising. Phase 1 sequential mode passes this through
      the Session; the action block is NOT executed at registration
      time (§108).
    - `live_value_registry`: when set, declared-live-value names are
      visible to the analyzer (live_value_names) for the §111 ownership
      checks; Phase 1 `remember` of a declared name transitions the
      registry entry to "active" (§117).
    """
    if isinstance(ast, WhenNode):
        return _execute_when(ast, symbol_table, handler_table, live_value_registry)
    if isinstance(ast, SequenceNode):
        return _execute_sequence(
            ast, symbol_table,
            handler_table=handler_table,
            live_value_registry=live_value_registry,
        )
    return _execute_single(
        ast, symbol_table,
        handler_table=handler_table,
        live_value_registry=live_value_registry,
    )


def _execute_when(
    node: WhenNode,
    symtab: dict[str, SymbolEntry],
    handler_table: HandlerTable | None,
    live_value_registry: LiveValueRegistry | None,
) -> LiminateResult:
    """Phase 1 WhenNode handling (v3a §108): validate condition + unless
    against the current symbol table, then register the handler. The
    action block is NOT executed here — Phase 2 fires it (§107)."""
    live_value_names = (
        live_value_registry.names() if live_value_registry is not None else None
    )
    analysis = analyze(
        node, symtab,
        live_value_names=live_value_names,
    )
    if isinstance(analysis, LiminateResult):
        if analysis.canonical is None:
            try:
                analysis.canonical = render(node)
            except Exception:
                pass
        return analysis
    if handler_table is None:
        # `when` outside a listener-capable Session can't be registered.
        # This is a programmer-facing error, not a user-facing one — the
        # CLI and Session always provide a handler table when a Phase 1
        # source contains `when` blocks.
        return LiminateResult(
            status=ResultStatus.ERROR_SEMANTIC,
            canonical=render(node),
            message=(
                "'when' handlers require a listener-capable Session. "
                "Run the program through `python -m liminate` rather "
                "than the bare `execute()` API."
            ),
            executed=False,
        )
    handler_table.register(node)
    return LiminateResult(
        status=ResultStatus.SUCCESS,
        canonical=render(node),
        output=None,
        executed=True,
    )


# ---------------------------------------------------------------------------
# Per-op execution
# ---------------------------------------------------------------------------


class _RuntimeError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class _FinishRequested(Exception):
    """v3a §112 — `finish` is "immediate and total." We propagate it as
    an exception so it unwinds out of nested structures (choose
    branches, composition bodies, sequence operations) up to the
    listener's `_fire_handler`, which catches it and transitions to
    shutdown. The exception carries no payload — the listener already
    knows which handler was firing."""


class _RequirementNotMet(Exception):
    """Normative Era batch 2 — raised when a `require` condition
    evaluates false. Surfaced to callers as REQUIREMENT_NOT_MET. The
    exception unwinds through nested sequences, compositions, and
    `choose` branches so prior committed operations stay committed
    under stepwise semantics (v1d §56).

    Invariant-readiness: carries optional structured `failure_metadata`
    (verb, condition, actual values) for machine-readable failure
    identity on the surfaced result."""
    def __init__(self, message: str, metadata: dict | None = None):
        super().__init__(message)
        self.message = message
        self.failure_metadata = metadata or {}


class _ProhibitionViolated(Exception):
    """Deontic Era — raised when a `forbid` condition evaluates true.
    Surfaced to callers as PROHIBITION_VIOLATED. Same unwind semantics
    as _RequirementNotMet: stepwise operations stay committed.

    Invariant-readiness: carries optional structured `failure_metadata`
    (verb, condition, actual values) for machine-readable failure
    identity on the surfaced result."""
    def __init__(self, message: str, metadata: dict | None = None):
        super().__init__(message)
        self.message = message
        self.failure_metadata = metadata or {}


class _PackVerbFailure(Exception):
    """Raised when a pack verb's verification check finds a mismatch.
    Surfaced as PACK_VERB_FAILURE. Carries structured metadata for
    machine-readable failure identity."""
    def __init__(self, message: str, metadata: dict):
        super().__init__(message)
        self.message = message
        self.failure_metadata = metadata


def _execute_single(
    node: ASTNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any = None,
    *,
    handler_table: HandlerTable | None = None,
    live_value_registry: LiveValueRegistry | None = None,
) -> LiminateResult:
    live_value_names = (
        live_value_registry.names() if live_value_registry is not None else None
    )
    analysis = analyze(node, symtab, live_value_names=live_value_names)
    if isinstance(analysis, LiminateResult):
        # Attach canonical if it's missing — we can render any AST.
        if analysis.canonical is None:
            try:
                analysis.canonical = render(node)
            except Exception:
                pass
        return analysis
    try:
        output = _exec_op(node, symtab, current_item)
    except _RuntimeError as e:
        return LiminateResult(
            status=ResultStatus.ERROR_SEMANTIC,
            canonical=render(node),
            message=e.message,
            executed=False,
        )
    except _RequirementNotMet as e:
        result = LiminateResult(
            status=ResultStatus.REQUIREMENT_NOT_MET,
            canonical=render(node),
            message=e.message,
            executed=False,
        )
        if e.failure_metadata:
            result.metadata = e.failure_metadata
        return result
    except _ProhibitionViolated as e:
        result = LiminateResult(
            status=ResultStatus.PROHIBITION_VIOLATED,
            canonical=render(node),
            message=e.message,
            executed=False,
        )
        if e.failure_metadata:
            result.metadata = e.failure_metadata
        return result
    except _PackVerbFailure as e:
        result = LiminateResult(
            status=ResultStatus.PACK_VERB_FAILURE,
            canonical=render(node),
            message=e.message,
            executed=False,
        )
        result.metadata = e.failure_metadata
        # Preserve pack attribution (Receipts v5 §15 dim. 3).
        if isinstance(node, PackVerbNode):
            owner = get_pack_verb_owner(node.word)
            if owner is not None:
                result.metadata["pack"] = owner
        return result
    _mark_live_value_active_if_remember(node, live_value_registry)
    result = LiminateResult(
        status=ResultStatus.SUCCESS,
        canonical=render(node),
        output=output if output else None,
        executed=True,
    )
    # Receipts v5 §15 dim. 3 — attribute pack-verb results to the pack
    # that contributed the verb. Base verbs leave the key absent.
    if isinstance(node, PackVerbNode):
        owner = get_pack_verb_owner(node.word)
        if owner is not None:
            if result.metadata is None:
                result.metadata = {}
            result.metadata["pack"] = owner
    return result


def _execute_sequence(
    seq: SequenceNode,
    symtab: dict[str, SymbolEntry],
    *,
    handler_table: HandlerTable | None = None,
    live_value_registry: LiveValueRegistry | None = None,
) -> LiminateResult:
    live_value_names = (
        live_value_registry.names() if live_value_registry is not None else None
    )
    completed_canonicals: list[str] = []
    outputs: list[str] = []
    for op in seq.operations:
        analysis = analyze(op, symtab, live_value_names=live_value_names)
        if isinstance(analysis, LiminateResult):
            return _stepwise_error(op, analysis, completed_canonicals, outputs, seq)
        try:
            op_output = _exec_op(op, symtab)
        except _RuntimeError as e:
            return _stepwise_error(
                op,
                LiminateResult(
                    status=ResultStatus.ERROR_SEMANTIC,
                    message=e.message,
                ),
                completed_canonicals,
                outputs,
                seq,
            )
        except _RequirementNotMet as e:
            fail_result = LiminateResult(
                status=ResultStatus.REQUIREMENT_NOT_MET,
                message=e.message,
            )
            if e.failure_metadata:
                fail_result.metadata = e.failure_metadata
            return _stepwise_error(
                op, fail_result, completed_canonicals, outputs, seq,
            )
        except _ProhibitionViolated as e:
            fail_result = LiminateResult(
                status=ResultStatus.PROHIBITION_VIOLATED,
                message=e.message,
            )
            if e.failure_metadata:
                fail_result.metadata = e.failure_metadata
            return _stepwise_error(
                op, fail_result, completed_canonicals, outputs, seq,
            )
        except _PackVerbFailure as e:
            fail_result = LiminateResult(
                status=ResultStatus.PACK_VERB_FAILURE,
                message=e.message,
            )
            fail_result.metadata = e.failure_metadata
            if isinstance(op, PackVerbNode):
                owner = get_pack_verb_owner(op.word)
                if owner is not None:
                    fail_result.metadata["pack"] = owner
            return _stepwise_error(
                op, fail_result, completed_canonicals, outputs, seq,
            )
        _mark_live_value_active_if_remember(op, live_value_registry)
        completed_canonicals.append(render(op))
        if op_output:
            outputs.extend(op_output)
    return LiminateResult(
        status=ResultStatus.SUCCESS,
        canonical=render(seq),
        output=outputs if outputs else None,
        executed=True,
    )


def _mark_live_value_active_if_remember(
    node: ASTNode,
    live_value_registry: LiveValueRegistry | None,
) -> None:
    """v3a §117: Phase 1 `remember <live-value> with V` transitions the
    registry entry from "unset" to "active". The interpreter calls this
    after a successful op so the change is committed only when the
    storage succeeded."""
    if live_value_registry is None:
        return
    if isinstance(
        node,
        (RememberValueNode, RememberListNode, RememberRecordNode),
    ):
        if node.name in live_value_registry:
            live_value_registry.mark_active(node.name)


def _stepwise_error(
    failed_op: ASTNode,
    failure: LiminateResult,
    completed_canonicals: list[str],
    outputs: list[str],
    seq: SequenceNode,
) -> LiminateResult:
    """Build the v1d §56 stepwise-failure message."""
    inner = (failure.message or "").strip()
    # Trim leading capital so the inner message blends after "but then".
    # Exception: preserve the pronoun "I" (e.g., "I can't find ..."), which
    # would otherwise read as "but then i can't find ...".
    if inner.startswith("I ") or inner == "I":
        inner_lower = inner
    else:
        inner_lower = inner[:1].lower() + inner[1:] if inner else inner

    if completed_canonicals:
        prior = completed_canonicals[-1]
        msg = f"I completed '{prior}' but then {inner_lower}"
        if not msg.endswith("."):
            msg += "."
        # If any committed op was a state-modifying filter, surface that fact.
        if any(_is_filter_canonical(c) for c in completed_canonicals):
            msg += " The filter has already been applied."
    else:
        msg = failure.message
    result = LiminateResult(
        status=failure.status,
        canonical=render(seq),
        output=outputs if outputs else None,
        message=msg,
        executed=False,
    )
    # Invariant-readiness: carry the structured failure identity
    # (verb / condition / actual / pack) through the stepwise wrapper so
    # downstream consumers see the same metadata on a sequence failure as
    # on a single-statement failure.
    if failure.metadata:
        result.metadata = failure.metadata
    return result


def _is_filter_canonical(canonical: str) -> bool:
    return canonical.startswith("filter ")


# ---------------------------------------------------------------------------
# Operation dispatch
# ---------------------------------------------------------------------------


def _exec_op(
    node: ASTNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any = None,
) -> list[str]:
    if isinstance(node, RememberValueNode):
        return _exec_remember_value(node, symtab, current_item)
    if isinstance(node, RememberListNode):
        return _exec_remember_list(node, symtab, current_item)
    if isinstance(node, RememberRecordNode):
        return _exec_remember_record(node, symtab, current_item)
    if isinstance(node, RememberCompositionNode):
        return _exec_remember_composition(node, symtab)
    if isinstance(node, ShowNode):
        return _exec_show(node, symtab, current_item)
    if isinstance(node, FilterNode):
        return _exec_filter(node, symtab)
    if isinstance(node, KeepNode):
        return _exec_keep(node, symtab)
    if isinstance(node, CountNode):
        return _exec_count(node, symtab)
    if isinstance(node, GatherNode):
        return _exec_gather(node, symtab)
    if isinstance(node, CombineNode):
        return _exec_combine(node, symtab)
    if isinstance(node, EachNode):
        return _exec_each(node, symtab)
    if isinstance(node, ChooseNode):
        # v2d §99–§101 — first matching branch fires; later branches and
        # actions are not evaluated. Pass `current_item` through so that
        # a `choose` reached as an inner step of a multi-statement action
        # within `each` still has the iterator (parse-time forbids
        # `each ... choose` at the top of an `each` body, but the action
        # *of a choose branch* may legitimately be invoked while a
        # `current_item` is in scope for the surrounding caller).
        return _exec_choose(node, symtab, current_item)
    if isinstance(node, CompositionCallNode):
        return _exec_composition_call(node, symtab)
    if isinstance(node, PackVerbNode):
        return _exec_pack_verb(node, symtab)
    if isinstance(node, AddNode):
        return _exec_add(node, symtab, current_item)
    if isinstance(node, RemoveNode):
        return _exec_remove(node, symtab, current_item)
    if isinstance(node, WeakensNode):
        return _exec_weakens(node, symtab)
    if isinstance(node, RequireNode):
        return _exec_require(node, symtab, current_item)
    if isinstance(node, RequireEachNode):
        return _exec_require_each(node, symtab)
    if isinstance(node, ForbidNode):
        return _exec_forbid(node, symtab, current_item)
    if isinstance(node, PermitNode):
        return _exec_permit(node, symtab, current_item)
    if isinstance(node, ExpectNode):
        return _exec_expect(node, symtab, current_item)
    if isinstance(node, AssignNode):
        return _exec_assign(node, symtab, current_item)
    if isinstance(node, SortNode):
        return _exec_sort(node, symtab)
    if isinstance(node, CompareNode):
        return _exec_compare(node, symtab, current_item)
    if isinstance(node, TransformNode):
        return _exec_transform(node, symtab)
    if isinstance(node, FinishNode):
        # v3a §112 — immediate and total. The exception unwinds out of
        # any surrounding choose/sequence/composition straight to the
        # listener. Phase 1 sequential execution should have rejected
        # `finish` at analyze time before reaching here.
        raise _FinishRequested()
    if isinstance(node, SequenceNode):
        # Nested sequence (e.g. inside a composition body). Re-analyze
        # per op for stepwise semantics (v1d §56); read the listener's
        # action-block context if we're inside one (v3a §111/§112).
        outputs: list[str] = []
        for op in node.operations:
            analysis = analyze(
                op, symtab,
                in_action_block=_in_action_block.get(),
                live_value_names=_live_value_names_ctx.get(),
            )
            if isinstance(analysis, LiminateResult):
                raise _RuntimeError(analysis.message or "")
            outputs.extend(_exec_op(op, symtab, current_item) or [])
        return outputs
    raise _RuntimeError(f"unsupported AST node {type(node).__name__}")


# ---------------------------------------------------------------------------
# remember
# ---------------------------------------------------------------------------


def _exec_remember_value(
    node: RememberValueNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    value = _evaluate_expression(node.value, symtab, current_item)
    _store(symtab, node.name, value, descriptor=node.descriptor)
    return []


def _exec_remember_list(
    node: RememberListNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    items = [
        copy.deepcopy(_evaluate_expression(it, symtab, current_item))
        for it in node.items
    ]
    # U2: capture the source-record names for each item so a later
    # schema-mismatch error can name the offending record. Only items
    # that referenced a named record in the symbol table get a name;
    # literal-value items or string-values stay None.
    source_names: list[str | None] = []
    has_named = False
    for it in node.items:
        if isinstance(it, BareWord) and it.word in symtab and symtab[it.word].type == "record":
            source_names.append(it.word)
            has_named = True
        else:
            source_names.append(None)
    _store(
        symtab,
        node.name,
        items,
        source_names=source_names if has_named else None,
        descriptor=node.descriptor,
    )
    return []


def _exec_remember_record(
    node: RememberRecordNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    fields: dict[str, Any] = {}
    schema: dict[str, str] = {}
    for fname, fexpr in node.fields:
        v = _evaluate_expression(fexpr, symtab, current_item)
        fields[fname] = v
        schema[fname] = _scalar_type(v)
    symtab[node.name] = SymbolEntry(
        name=node.name,
        value=fields,
        type="record",
        schema=schema,
        descriptor=node.descriptor,
    )
    return []


# ---------------------------------------------------------------------------
# v4a §137 — pack verb dispatch
# ---------------------------------------------------------------------------


def _exec_pack_verb(
    node: PackVerbNode,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    """v2 — dispatch by execution type via isinstance."""
    execution = node.signature.execution
    if isinstance(execution, SetValueExecution):
        return _exec_pack_set_value(node, execution, symtab)
    if isinstance(execution, SubstringCheckExecution):
        return _exec_pack_substring_check(node, execution, symtab)
    if isinstance(execution, AppendToListExecution):
        return _exec_pack_append_to_list(node, execution, symtab)
    if isinstance(execution, SetFieldExecution):
        return _exec_pack_set_field(node, execution, symtab)
    if isinstance(execution, CompareValuesExecution):
        return _exec_pack_compare_values(node, execution, symtab)
    if isinstance(execution, NumericExtractCompareExecution):
        return _exec_pack_numeric_extract_compare(node, execution, symtab)
    raise _RuntimeError(
        f"Pack verb '{node.word}' has an unrecognized execution type."
    )


def _resolve_target(execution, node: PackVerbNode, symtab) -> str:
    """v2 §8 — resolve the symbol name to write to. `target_slot` wins
    over `target_name` (load-time validation guarantees exactly one is
    non-None for write-target executions)."""
    if execution.target_slot is not None:
        value_node = node.slot_values.get(execution.target_slot)
        if isinstance(value_node, NameRef):
            return value_node.name
        if isinstance(value_node, BareWord):
            return value_node.word
        raise _RuntimeError(
            f"Pack verb '{node.word}' needs a name for its target, "
            f"not a literal value."
        )
    return execution.target_name


def _resolve_source(execution, node: PackVerbNode, symtab) -> Any:
    """v2 §8 — resolve the value to write. `source_slot` is evaluated via
    `_evaluate_expression`; `literal_value` is returned as-is."""
    if execution.source_slot is not None:
        value_node = node.slot_values.get(execution.source_slot)
        return _evaluate_expression(value_node, symtab, None)
    return execution.literal_value


def _exec_pack_set_value(
    node: PackVerbNode,
    execution: SetValueExecution,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    """v2 §8 — set_value with name-vs-value special case preserved:
    when source_slot resolves to a NameRef, store the *name string* (so
    `navigate to settings` stores `"settings"`, not the screen record's
    contents). For literal_value, store the literal directly."""
    target_name = _resolve_target(execution, node, symtab)
    if execution.source_slot is not None:
        value_node = node.slot_values.get(execution.source_slot)
        if isinstance(value_node, NameRef):
            value: Any = value_node.name
        else:
            value = _evaluate_expression(value_node, symtab, None)
    else:
        value = execution.literal_value
    _store(symtab, target_name, value)
    return []


def _exec_pack_substring_check(
    node: PackVerbNode,
    execution: SubstringCheckExecution,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    """v2 §4 — case-sensitive substring containment."""
    check_node = node.slot_values.get(execution.check_slot)
    against_node = node.slot_values.get(execution.against_slot)
    check_raw = _evaluate_expression(check_node, symtab, None)
    check_value = _format_scalar(check_raw)
    against_value = _evaluate_expression(against_node, symtab, None)
    if not isinstance(against_value, str):
        against_value = _format_scalar(against_value)
    if check_value not in against_value:
        against_name = (
            against_node.name if isinstance(against_node, NameRef)
            else execution.against_slot
        )
        preview = against_value[:80]
        suffix = "..." if len(against_value) > 80 else ""
        raise _PackVerbFailure(
            f"The text '{check_value}' was not found in '{against_name}'. "
            f"The source begins: '{preview}{suffix}'",
            metadata={
                "verb": node.word,
                "failure_type": "substring_not_found",
                "check_value": check_value,
                "against_name": against_name,
            },
        )
    return []


def _exec_pack_append_to_list(
    node: PackVerbNode,
    execution: AppendToListExecution,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    """v2 §5 — deep-copy append to a list."""
    target_name = _resolve_target(execution, node, symtab)
    resolved_value = _resolve_source(execution, node, symtab)
    entry = symtab[target_name]
    # v1 §7 `none` placeholder seed pattern — clear the sentinel on first add.
    if (
        entry.type == "list_of_strings"
        and len(entry.value) == 1
        and entry.value == ["none"]
    ):
        entry.value.clear()
        new_type, new_schema = _infer_type_and_schema([resolved_value])
        entry.type = new_type
        entry.schema = new_schema
    entry.value.append(copy.deepcopy(resolved_value))
    return []


def _exec_pack_set_field(
    node: PackVerbNode,
    execution: SetFieldExecution,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    """v2 §6 — set one field on a record. Creates the field if absent."""
    target_name = _resolve_target(execution, node, symtab)
    resolved_value = _resolve_source(execution, node, symtab)
    entry = symtab[target_name]
    entry.value[execution.field_name] = copy.deepcopy(resolved_value)
    if entry.schema is None:
        entry.schema = {}
    entry.schema[execution.field_name] = _scalar_type(resolved_value)
    return []


def _exec_pack_compare_values(
    node: PackVerbNode,
    execution: CompareValuesExecution,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    """v2 §7 — compare two slot values; store status (and details for
    structural mode); raise on mismatch when on_mismatch == 'error'."""
    left_node = node.slot_values.get(execution.left_slot)
    right_node = node.slot_values.get(execution.right_slot)
    left_value = _evaluate_expression(left_node, symtab, None)
    right_value = _evaluate_expression(right_node, symtab, None)
    left_name = (
        left_node.name if isinstance(left_node, NameRef)
        else execution.left_slot
    )
    right_name = (
        right_node.name if isinstance(right_node, NameRef)
        else execution.right_slot
    )

    status: str
    details: list[Any] = []

    if execution.comparison == "equality":
        status = "match" if left_value == right_value else "mismatch"
    else:  # structural
        l_is_record = isinstance(left_value, dict)
        r_is_record = isinstance(right_value, dict)
        l_is_list = isinstance(left_value, list)
        r_is_list = isinstance(right_value, list)
        if l_is_record and r_is_record:
            divergent: list[str] = []
            for k in left_value:
                if k not in right_value or left_value[k] != right_value[k]:
                    divergent.append(k)
            for k in right_value:
                if k not in left_value and k not in divergent:
                    divergent.append(k)
            status = "match" if not divergent else "mismatch"
            details = divergent
        elif l_is_list and r_is_list:
            if len(left_value) != len(right_value):
                status = "length_mismatch"
                details = []
            else:
                indices = [
                    i for i, (a, b) in enumerate(zip(left_value, right_value))
                    if a != b
                ]
                status = "match" if not indices else "mismatch"
                details = indices
        elif type(left_value) is type(right_value):
            status = "match" if left_value == right_value else "mismatch"
        else:
            status = "type_mismatch"
            details = []

    # Symbol table writes stay for handler visibility — a `when` handler
    # watching `verification-status`/`verification-divergences` needs the
    # value committed before the failure exception unwinds (§8 mode 1).
    _store(symtab, execution.status_target, status)
    if execution.details_target is not None:
        _store(symtab, execution.details_target, list(details))

    # Invariant-readiness: any non-match outcome surfaces as
    # PACK_VERB_FAILURE, regardless of the pack's on_mismatch mode. This
    # subsumes the former on_mismatch == "error" raise block — the result
    # stream, not the symbol table, is now the source of truth for failure.
    if status != "match":
        raise _PackVerbFailure(
            f"'{left_name}' does not match '{right_name}'. Status: {status}.",
            metadata={
                "verb": node.word,
                "failure_type": f"comparison_{status}",
                "left_name": left_name,
                "right_name": right_name,
                "status": status,
                "divergences": list(details) if details else [],
            },
        )
    return []


def _exec_pack_numeric_extract_compare(
    node: PackVerbNode,
    execution: NumericExtractCompareExecution,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    """Sixth execution type: extract all numbers from a source string,
    find the closest to the claimed value, check tolerance."""
    check_node = node.slot_values.get(execution.check_slot)
    against_node = node.slot_values.get(execution.against_slot)
    tolerance_node = node.slot_values.get(execution.tolerance_slot)

    claimed = _evaluate_expression(check_node, symtab, None)
    source_text = _evaluate_expression(against_node, symtab, None)
    tolerance = _evaluate_expression(tolerance_node, symtab, None)

    if not isinstance(claimed, (int, float)):
        claimed = float(_format_scalar(claimed))
    if not isinstance(tolerance, (int, float)):
        tolerance = float(_format_scalar(tolerance))
    if not isinstance(source_text, str):
        source_text = _format_scalar(source_text)

    numbers = [float(m) for m in re.findall(r'-?\d+\.?\d*', source_text)]

    if not numbers:
        against_name = (
            against_node.name if isinstance(against_node, NameRef)
            else execution.against_slot
        )
        # Symbol table writes stay for handler visibility before the raise.
        _store(symtab, execution.status_target, "no_numbers_found")
        _store(symtab, execution.matched_target, "none")
        _store(symtab, execution.delta_target, "none")
        raise _PackVerbFailure(
            f"No numbers found in '{against_name}'.",
            metadata={
                "verb": node.word,
                "failure_type": "no_numbers_found",
                "against_name": against_name,
            },
        )

    closest = min(numbers, key=lambda n: abs(n - claimed))
    delta = abs(claimed - closest)

    if closest == int(closest):
        closest = int(closest)
    if delta == int(delta):
        delta = int(delta)

    within = delta <= tolerance
    status = "within_tolerance" if within else "outside_tolerance"
    _store(symtab, execution.status_target, status)
    _store(symtab, execution.matched_target, closest)
    _store(symtab, execution.delta_target, delta)

    # Invariant-readiness: outside-tolerance surfaces as PACK_VERB_FAILURE
    # regardless of on_mismatch mode. Writes above stay committed.
    if not within:
        against_name = (
            against_node.name if isinstance(against_node, NameRef)
            else execution.against_slot
        )
        raise _PackVerbFailure(
            f"Claimed {_format_scalar(claimed)} but closest value in "
            f"'{against_name}' is {_format_scalar(closest)} "
            f"(delta: {_format_scalar(delta)}, tolerance: "
            f"{_format_scalar(tolerance)}).",
            metadata={
                "verb": node.word,
                "failure_type": "outside_tolerance",
                "claimed": claimed,
                "closest": closest,
                "delta": delta,
                "tolerance": tolerance,
                "against_name": against_name,
            },
        )
    return []


def _exec_remember_composition(
    node: RememberCompositionNode,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    symtab[node.name] = SymbolEntry(
        name=node.name,
        value=node.body,
        type="composition",
        # v2d §96: preserve the declared parameter name so the §97
        # mismatch check and the §96 save/bind/exec/restore at call
        # time have the metadata they need.
        composition_param=node.param,
    )
    return []


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


def _exec_show(
    node: ShowNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    if node.target is None:
        # Iterator-driven: show the current item itself.
        return _display_lines(current_item)
    if isinstance(node.target, QuotedString):
        # v2c §88 — literal display: emit the quoted content verbatim,
        # no symbol-table lookup.
        return [node.target.content]
    name = node.target.name
    # v2a §68 (D4): `show <field> of <record>` — extract the named field
    # from the named record. Semantic checks (record exists, is a record,
    # has the field) already ran in the analyzer.
    if node.record_name is not None:
        record = symtab[node.record_name].value
        # A field may itself be a list (e.g. the `divergences` field of a
        # `comparison` record). Use the list display format rather than
        # Python's repr so it reads as `status, total`, not `['status',
        # 'total']`.
        field_value = record[name]
        if isinstance(field_value, list):
            return _display_lines(field_value)
        return [_format_scalar(field_value)]
    # v2a §69 (D1): multi-field display inside `each ... show`.
    if node.extra_fields and isinstance(current_item, dict):
        fields = [name, *node.extra_fields]
        parts = [f"{f}: {_format_scalar(current_item[f])}" for f in fields]
        return [", ".join(parts)]
    # Iterator-first resolution (v1c §49).
    if isinstance(current_item, dict) and name in current_item:
        return [_format_scalar(current_item[name])]
    entry = symtab[name]
    return _display_lines(entry.value)


# ---------------------------------------------------------------------------
# filter / count / gather / combine
# ---------------------------------------------------------------------------


def _exec_filter(node: FilterNode, symtab: dict[str, SymbolEntry]) -> list[str]:
    entry = symtab[node.target.name]
    kept = [item for item in entry.value if _eval_condition(node.condition, item, symtab)]
    entry.value[:] = kept  # in-place per §24 line 478
    return []


def _exec_sort(node: SortNode, symtab: dict[str, SymbolEntry]) -> list[str]:
    """Infrastructure Era batch 2 — in-place sort by a record field.

    Silent like `filter`. Empty lists are a no-op. Non-record items
    surface as runtime errors so the user gets a clear message instead
    of a Python exception. Mixed-type field values (some numeric, some
    text) raise TypeError under Python's stable sort — caught and
    re-raised as a runtime error.
    """
    entry = symtab[node.target.name]
    the_list = entry.value
    if not the_list:
        return []
    for i, item in enumerate(the_list):
        if not isinstance(item, dict):
            raise _RuntimeError(
                f"I can only sort a list of records by a field. "
                f"Item {i + 1} in '{node.target.name}' is "
                f"{_format_scalar(item)}."
            )
        if node.field not in item:
            raise _RuntimeError(
                f"Record {i + 1} in '{node.target.name}' doesn't "
                f"have a field called '{node.field}'."
            )
    try:
        the_list.sort(
            key=lambda r: r[node.field],
            reverse=node.descending,
        )
    except TypeError:
        raise _RuntimeError(
            f"I can't sort '{node.target.name}' by '{node.field}' — "
            f"the values are a mix of types that can't be compared."
        )
    return []


def _exec_transform(
    node: TransformNode,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    """Final V2 promotion — per-element in-place list mutation.

    Record-field mode (`node.field` set): re-evaluate the expression for
    each record with that record as the iterator context and write the
    result back to the named field. Scalar-list mode (`node.field` None):
    re-evaluate the expression with the current scalar element as the
    iterator context (the `each` pronoun resolves to it) and replace the
    element.

    The per-element evaluator is `_eval_arithmetic_operand`, which
    resolves a bare field name against the current record dict and
    delegates everything else (arithmetic, field access, the `each`
    pronoun, symbol-table names) to `_evaluate_expression` — the same
    iterator-context resolution `each`/`where`/`add` use. Silent.
    """
    entry = symtab[node.target.name]
    the_list = entry.value
    if not the_list:
        return []

    if node.field is not None:
        for i, item in enumerate(the_list):
            if not isinstance(item, dict):
                raise _RuntimeError(
                    f"I can only transform fields on records. "
                    f"Item {i + 1} in '{node.target.name}' is "
                    f"{_format_scalar(item)}."
                )
            if node.field not in item:
                raise _RuntimeError(
                    f"Record {i + 1} in '{node.target.name}' doesn't "
                    f"have a field called '{node.field}'."
                )
            item[node.field] = _eval_arithmetic_operand(
                node.expression, symtab, item,
            )
    else:
        for i in range(len(the_list)):
            the_list[i] = _eval_arithmetic_operand(
                node.expression, symtab, the_list[i],
            )
    return []


def _exec_compare(
    node: CompareNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    """V2 promotion — compare two domain values and store a structured
    `comparison` record. Comparison mode is inferred from operand types:

    - record vs record  → structural; divergences = sorted diverging keys
    - list vs list       → structural; divergences = diverging indices
      (length_mismatch when lengths differ)
    - record/list vs the other shape, or a container vs a scalar
                         → type_mismatch
    - scalar vs scalar   → equality; divergences = []

    `_evaluate_expression` resolves DecayingValue operands to their
    current decayed value, so decay-wrapped numbers compare on their
    effective value. Silent — no output; result stored only.
    """
    left_val = _evaluate_expression(node.left, symtab, current_item)
    right_val = _evaluate_expression(node.right, symtab, current_item)

    left_is_dict = isinstance(left_val, dict)
    right_is_dict = isinstance(right_val, dict)
    left_is_list = isinstance(left_val, list)
    right_is_list = isinstance(right_val, list)

    divergences: list[Any]
    if left_is_dict and right_is_dict:
        all_keys = set(left_val) | set(right_val)
        diverging = [
            k for k in sorted(all_keys)
            if k not in left_val or k not in right_val
            or left_val[k] != right_val[k]
        ]
        status = "match" if not diverging else "mismatch"
        divergences = diverging
    elif left_is_list and right_is_list:
        if len(left_val) != len(right_val):
            status = "length_mismatch"
            divergences = []
        else:
            diverging_idx = [
                i for i, (l, r) in enumerate(zip(left_val, right_val))
                if l != r
            ]
            status = "match" if not diverging_idx else "mismatch"
            divergences = diverging_idx
    elif left_is_dict != right_is_dict or left_is_list != right_is_list:
        # One operand is a record/list and the other is a different
        # shape (or a scalar).
        status = "type_mismatch"
        divergences = []
    else:
        status = "match" if left_val == right_val else "mismatch"
        divergences = []

    _store(symtab, "comparison", {"status": status, "divergences": divergences})
    return []


def _exec_keep(node: KeepNode, symtab: dict[str, SymbolEntry]) -> list[str]:
    """v2a §67 — non-destructive filter.

    Walks the source list and collects matching items into a fresh list.
    The source entry in the symbol table is untouched. Auto-shows the
    matching items unless the surrounding context captured the result
    via `remember ... from keep ...` (the recursive-descent §43 path
    routes through _evaluate_expression below, which bypasses this
    function's output).
    """
    entry = symtab[node.target.name]
    kept = [
        copy.deepcopy(item)
        for item in entry.value
        if _eval_condition(node.condition, item, symtab)
    ]
    return _display_lines(kept)


def _exec_count(node: CountNode, symtab: dict[str, SymbolEntry]) -> list[str]:
    entry = symtab[node.target.name]
    return [str(len(entry.value))]


def _exec_gather(node: GatherNode, symtab: dict[str, SymbolEntry]) -> list[str]:
    start = int(node.from_val)
    stop = int(node.to_val)
    items = list(range(start, stop + 1))
    _store(symtab, node.name, items)
    # v1b §40: gather both stores AND auto-shows.
    return _display_lines(items)


def _exec_add(
    node: AddNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    """Liminate `add` v1 §4 / §10 — in-place append with deep-copy.

    Iterator-first resolution for BareWord items (v1c §49): inside
    `each <list-of-records> add <field> to <other-list>`, a bare name
    that is a field on the current record resolves to that field's
    value, matching the analyzer's iterator-aware type inference.
    """
    entry = symtab[node.target.name]
    item_node = node.item
    if (
        isinstance(item_node, BareWord)
        and isinstance(current_item, dict)
        and item_node.word in current_item
    ):
        item_value: Any = current_item[item_node.word]
    else:
        item_value = _evaluate_expression(item_node, symtab, current_item)
    # On first add to an empty list or a `none`-seeded list, re-infer the
    # element type from the first real value. Mirrors _exec_pack_append_to_list.
    if not entry.value or (
        entry.type == "list_of_strings"
        and len(entry.value) == 1
        and entry.value == ["none"]
    ):
        entry.value.clear()
        new_type, new_schema = _infer_type_and_schema([item_value])
        entry.type = new_type
        entry.schema = new_schema
    entry.value.append(copy.deepcopy(item_value))
    return []


def _exec_remove(
    node: RemoveNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    """Retract an item from an existing list — first-occurrence removal.

    Iterator-first resolution for BareWord items (mirrors `_exec_add`):
    inside an `each` over records, a bare name that is a field on the
    current record resolves to that field's value. Errors if the item
    is not in the list — `remove` is explicit, not silent.
    """
    entry = symtab[node.target.name]
    item_node = node.item
    if (
        isinstance(item_node, BareWord)
        and isinstance(current_item, dict)
        and item_node.word in current_item
    ):
        item_value: Any = current_item[item_node.word]
    else:
        item_value = _evaluate_expression(item_node, symtab, current_item)
    if item_value not in entry.value:
        raise _RuntimeError(
            f"I can't find '{_format_scalar(item_value)}' in "
            f"'{node.target.name}'."
        )
    entry.value.remove(item_value)
    return []


def _exec_weakens(
    node: WeakensNode,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    """Metabolic Era batch 1 — attach decay metadata to a numeric variable.

    If the variable is already a DecayingValue, reapplication is
    last-wins: new period, ticks reset, initial value taken from the
    current decayed value at the moment of reapplication.
    """
    entry = symtab[node.subject.name]
    current = entry.value
    period = node.period.value

    if isinstance(current, DecayingValue):
        current = current.current_value

    if not isinstance(current, (int, float)):
        raise _RuntimeError(
            f"'weakens' only works on numbers — "
            f"'{node.subject.name}' is a {type(current).__name__}."
        )

    entry.value = DecayingValue(
        initial_value=float(current),
        period=period,
    )
    # Type stays "number" — a DecayingValue IS a number with metadata.
    return []


def _exec_require(
    node: RequireNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    """Normative Era batch 2 — evaluate the condition. Silent on pass;
    raises _RequirementNotMet on fail. The error message echoes the
    condition in canonical form and reports the actual value(s) that
    violated the rule for the first failing sub-condition (helpful for
    diagnosis when conditions are compound).
    """
    if _eval_condition(node.condition, current_item, symtab):
        return []
    condition_text = render(node.condition)
    actual = _condition_actual_values(node.condition, current_item, symtab)
    msg = f"Requirement not met: {condition_text}."
    if actual:
        msg += f" {actual}"
    raise _RequirementNotMet(msg, metadata={
        "verb": "require",
        "condition": condition_text,
        "actual": actual,
    })


def _exec_require_each(
    node: RequireEachNode,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    """v8a §49 — iterated enforcement. Evaluate the condition once per
    element in the collection, binding the current element under
    `binding_name` (a temporary symbol-table entry) and as the iterator
    `current_item`. Silent if every element passes; raises
    _RequirementNotMet identifying the first failing element otherwise.

    The temporary binding uses save/restore semantics (composition
    parameter pattern, v2d §96) so an existing symbol with the same name
    survives the require-each evaluation. The `finally` guarantees the
    binding never leaks, even when the condition fails or an unexpected
    error unwinds the loop.
    """
    the_list = symtab[node.collection.name].value

    saved = symtab.get(node.binding_name)
    try:
        for i, item in enumerate(the_list):
            item_type, item_schema = _infer_type_and_schema(item)
            symtab[node.binding_name] = SymbolEntry(
                name=node.binding_name,
                value=item,
                type=item_type,
                schema=item_schema,
            )
            if not _eval_condition(node.condition, item, symtab):
                condition_text = render(node.condition)
                actual = _condition_actual_values(node.condition, item, symtab)
                # 1-indexed for human readability.
                msg = (
                    f"Requirement not met: require each {node.binding_name} "
                    f"in {node.collection.name} {condition_text}. "
                    f"Failed at element {i + 1}."
                )
                if actual:
                    msg += f" {actual}"
                raise _RequirementNotMet(msg, metadata={
                    "verb": "require",
                    "iteration": "each",
                    "binding": node.binding_name,
                    "collection": node.collection.name,
                    "element_index": i,
                    "condition": condition_text,
                    "actual": actual,
                })
    finally:
        if saved is not None:
            symtab[node.binding_name] = saved
        else:
            symtab.pop(node.binding_name, None)

    return []


def _exec_forbid(
    node: ForbidNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    """Deontic Era — evaluate the condition. Silent on false (no
    prohibition triggered); raises _ProhibitionViolated on true.
    The error message echoes the condition in canonical form and
    reports the actual value(s) that triggered the prohibition.
    """
    if not _eval_condition(node.condition, current_item, symtab):
        return []
    condition_text = render(node.condition)
    actual = _condition_actual_values(node.condition, current_item, symtab)
    msg = f"Prohibition violated: {condition_text}."
    if actual:
        msg += f" {actual}"
    raise _ProhibitionViolated(msg, metadata={
        "verb": "forbid",
        "condition": condition_text,
        "actual": actual,
    })


def _exec_permit(
    node: PermitNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    """Deontic Era — evaluate the condition. If true, emit an output
    line recording the explicit permission. If false, silent pass.
    Never halts. The output message echoes the condition in canonical
    form and reports the actual value(s) that satisfied the permission.
    """
    if not _eval_condition(node.condition, current_item, symtab):
        return []
    condition_text = render(node.condition)
    actual = _condition_actual_values(node.condition, current_item, symtab)
    msg = f"Permitted: {condition_text}."
    if actual:
        msg += f" {actual}"
    return [msg]


def _exec_expect(
    node: ExpectNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    """Epistemic Era batch 3 — evaluate the condition. Silent on pass;
    on divergence, emit an output line reporting the condition and the
    actual value(s) of the first failing sub-condition. Program
    continues with SUCCESS — expectations are informational, not
    blocking.
    """
    if _eval_condition(node.condition, current_item, symtab):
        return []
    condition_text = render(node.condition)
    actual = _condition_actual_values(node.condition, current_item, symtab)
    msg = f"Expectation not met: {condition_text}."
    if actual:
        msg += f" {actual}"
    return [msg]


def _exec_assign(
    node: AssignNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    """Delegated Era batch 3 — store the item→recipient mapping in the
    symbol table. The item name becomes the variable name; the evaluated
    recipient becomes the value. Uses `_store` for all overwrite,
    reinforcement, type-inference, and copy-on-store semantics.
    """
    recipient_value = _evaluate_expression(node.recipient, symtab, current_item)
    _store(symtab, node.item.name, recipient_value)
    return []


def _condition_actual_values(
    cond: ASTNode,
    current_item: Any,
    symtab: dict[str, SymbolEntry],
) -> str:
    """Format the actual values of the first failing sub-condition.
    Used by both `_exec_require` (REQUIREMENT_NOT_MET error message)
    and `_exec_expect` (divergence output line). For compound `and`
    conditions, report the first failing branch; for `or`, report
    the left branch (both failed, so either is informative)."""
    if isinstance(cond, CompoundConditionNode):
        left_failed = not _eval_condition(cond.left, current_item, symtab)
        if cond.connector == "and":
            if left_failed:
                return _condition_actual_values(cond.left, current_item, symtab)
            return _condition_actual_values(cond.right, current_item, symtab)
        # "or" — both must have failed for us to reach here; report left.
        return _condition_actual_values(cond.left, current_item, symtab)
    if isinstance(cond, ConditionNode):
        try:
            field_val = _eval_field(cond.field, current_item, symtab)
        except _RuntimeError:
            return ""
        field_text = render(cond.field)
        return f"{field_text} is {_format_scalar(field_val)}."
    return ""


def decay_tick(symtab: dict[str, SymbolEntry]) -> list[str]:
    """Advance every DecayingValue entry by one tick.

    Adapters (or the listener) call this when a tick event occurs.
    Returns the names of variables that crossed from a positive value
    to zero this tick — useful as a strong handler-firing trigger.
    """
    reached_zero: list[str] = []
    for name, entry in symtab.items():
        if isinstance(entry.value, DecayingValue):
            was_positive = entry.value.current_value > 0.0
            entry.value.tick()
            if was_positive and entry.value.current_value == 0.0:
                reached_zero.append(name)
    return reached_zero


def _exec_combine(node: CombineNode, symtab: dict[str, SymbolEntry]) -> list[str]:
    entry = symtab[node.target.name]
    total = sum(entry.value)
    # Preserve integer-ness if all inputs were integers.
    return [_format_scalar(total)]


# ---------------------------------------------------------------------------
# each — iterator context (v1c §49)
# ---------------------------------------------------------------------------


def _exec_each(node: EachNode, symtab: dict[str, SymbolEntry]) -> list[str]:
    entry = symtab[node.collection.name]
    outputs: list[str] = []
    for item in entry.value:
        out = _exec_op(node.action, symtab, current_item=item)
        if out:
            outputs.extend(out)
    return outputs


# ---------------------------------------------------------------------------
# choose (v2d §99–§101)
# ---------------------------------------------------------------------------


def _exec_choose(
    node: ChooseNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> list[str]:
    """Evaluate branches in order, firing the first whose condition is
    true (or the terminal `otherwise` branch if no condition matches).
    Short-circuits per §101 — later branches do not evaluate."""
    for br in node.branches:
        if br.condition is None:
            return _exec_op(br.action, symtab, current_item) or []
        if _eval_condition(br.condition, current_item, symtab):
            return _exec_op(br.action, symtab, current_item) or []
    return []


# ---------------------------------------------------------------------------
# composition call — body executes against current symbol table (v1b §41)
# ---------------------------------------------------------------------------


def _exec_composition_call(
    node: CompositionCallNode,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    """Execute a composition call. v2d §96 binds the parameter (if any)
    to a deep copy of the passed argument for the duration of the body,
    then restores any shadowed global. The analyzer has already verified
    call-site shape (§97), so the binding has well-defined inputs."""
    snapshot = _bind_parameter(node, symtab)
    in_act = _in_action_block.get()
    live_names = _live_value_names_ctx.get()
    try:
        body = symtab[node.name].value
        if isinstance(body, SequenceNode):
            outputs: list[str] = []
            for op in body.operations:
                analysis = analyze(
                    op, symtab,
                    in_action_block=in_act,
                    live_value_names=live_names,
                )
                if isinstance(analysis, LiminateResult):
                    raise _RuntimeError(analysis.message or "")
                out = _exec_op(op, symtab)
                if out:
                    outputs.extend(out)
            return outputs
        analysis = analyze(
            body, symtab,
            in_action_block=in_act,
            live_value_names=live_names,
        )
        if isinstance(analysis, LiminateResult):
            raise _RuntimeError(analysis.message or "")
        return _exec_op(body, symtab) or []
    finally:
        _restore_parameter(snapshot, symtab)


def _bind_parameter(
    node: CompositionCallNode,
    symtab: dict[str, SymbolEntry],
) -> tuple[str | None, SymbolEntry | None, bool]:
    """v2d §96 — save the existing binding (if any), then bind the
    parameter name to a deep copy of the passed argument's value.

    Returns (param_name, saved_entry, was_present). Pass this tuple to
    `_restore_parameter` after body execution.
    """
    entry = symtab[node.name]
    param = entry.composition_param
    if param is None or node.arg is None:
        return None, None, False
    arg_entry = symtab[node.arg]
    saved = symtab.get(param)
    symtab[param] = SymbolEntry(
        name=param,
        value=copy.deepcopy(arg_entry.value),
        type=arg_entry.type,
        schema=copy.deepcopy(arg_entry.schema),
        source_names=(
            list(arg_entry.source_names)
            if arg_entry.source_names is not None
            else None
        ),
    )
    return param, saved, saved is not None


def _restore_parameter(
    snapshot: tuple[str | None, SymbolEntry | None, bool],
    symtab: dict[str, SymbolEntry],
) -> None:
    """v2d §96 — symmetric counterpart to `_bind_parameter`. Pops the
    parameter binding and (if any) restores the prior global entry."""
    param, saved, was_present = snapshot
    if param is None:
        return
    if was_present:
        symtab[param] = saved
    else:
        symtab.pop(param, None)


# ---------------------------------------------------------------------------
# Expression evaluation (values for `remember ... with` / `... from`,
# list items, record field values)
# ---------------------------------------------------------------------------


def _evaluate_expression(
    expr: ASTNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> Any:
    if isinstance(expr, NumberLiteral):
        return expr.value
    if isinstance(expr, BareWord):
        # If the word matches a symbol, copy its value (§24 line 486).
        # Otherwise treat the word as a string literal.
        if expr.word in symtab:
            val = symtab[expr.word].value
            if isinstance(val, DecayingValue):
                return val.current_value
            return copy.deepcopy(val)
        return expr.word
    if isinstance(expr, QuotedString):
        # v2c §86/§87 — quoted content is always a literal string. No
        # symbol-table fallback (unlike BareWord) — quotes mark data.
        return expr.content
    if isinstance(expr, NameRef):
        if expr.name in symtab:
            val = symtab[expr.name].value
            if isinstance(val, DecayingValue):
                return val.current_value
            return copy.deepcopy(val)
        raise _RuntimeError(
            f"I can't find '{expr.name}'. You might need to 'remember' it first."
        )
    if isinstance(expr, EachPronoun):
        return current_item
    if isinstance(expr, FieldAccessNode):
        # v2b §77: extract <field> of <record> as a value.
        record = symtab[expr.record_name].value
        return copy.deepcopy(record[expr.field])
    if isinstance(expr, ArithmeticNode):
        return _eval_arithmetic(expr, symtab, current_item)
    # Sub-operations that yield a value.
    if isinstance(expr, CombineNode):
        entry = symtab[expr.target.name]
        return sum(entry.value)
    if isinstance(expr, CountNode):
        entry = symtab[expr.target.name]
        return len(entry.value)
    if isinstance(expr, KeepNode):
        # v2a §67: `remember ... from keep ...` captures the matching list.
        # Source remains untouched — the recursive-descent §43 path uses
        # the value `keep` produces without invoking the auto-show in
        # _exec_keep above.
        entry = symtab[expr.target.name]
        return [
            copy.deepcopy(item)
            for item in entry.value
            if _eval_condition(expr.condition, item, symtab)
        ]
    if isinstance(expr, CompositionCallNode):
        # v2b §76 — execute the composition's body, returning the value
        # of its last operation. The analyzer has already verified the
        # last op is value-producing (void-result check fires before
        # exec, so side effects don't run in that case). Non-final ops
        # run for side effects per v1d §56 stepwise semantics.
        return _composition_call_value(expr, symtab)
    raise _RuntimeError(f"Can't evaluate {type(expr).__name__} as a value.")


def _composition_call_value(
    node: CompositionCallNode,
    symtab: dict[str, SymbolEntry],
) -> Any:
    """v2b §76 / v2d §96 + §98 — evaluate a composition call as a value
    expression. The parameter (if any) is bound for the body's execution
    and the last operation's value is returned per §76."""
    snapshot = _bind_parameter(node, symtab)
    in_act = _in_action_block.get()
    live_names = _live_value_names_ctx.get()
    try:
        body = symtab[node.name].value
        if isinstance(body, SequenceNode):
            ops = body.operations
            for op in ops[:-1]:
                analysis = analyze(
                    op, symtab,
                    in_action_block=in_act,
                    live_value_names=live_names,
                )
                if isinstance(analysis, LiminateResult):
                    raise _RuntimeError(analysis.message or "")
                _exec_op(op, symtab)
            last = ops[-1]
        else:
            last = body
        analysis = analyze(
            last, symtab,
            in_action_block=in_act,
            live_value_names=live_names,
        )
        if isinstance(analysis, LiminateResult):
            raise _RuntimeError(analysis.message or "")
        return _value_of_op(last, symtab)
    finally:
        _restore_parameter(snapshot, symtab)


def _value_of_op(op: ASTNode, symtab: dict[str, SymbolEntry]) -> Any:
    """Return the value produced by a value-producing last operation
    (v2b §76 table). Side effects required for the op's value (gather's
    storage, the from-form's symbol binding) still execute; pure side
    effects (auto-show, etc.) are suppressed because we go through the
    value extraction path rather than the standalone-op path."""
    if isinstance(op, KeepNode):
        entry = symtab[op.target.name]
        return [
            copy.deepcopy(item)
            for item in entry.value
            if _eval_condition(op.condition, item, symtab)
        ]
    if isinstance(op, CombineNode):
        return sum(symtab[op.target.name].value)
    if isinstance(op, CountNode):
        return len(symtab[op.target.name].value)
    if isinstance(op, GatherNode):
        start = int(op.from_val)
        stop = int(op.to_val)
        items = list(range(start, stop + 1))
        _store(symtab, op.name, items)
        return items
    if isinstance(op, RememberValueNode):
        # The remember-from-verb-phrase form: capture the value and
        # also bind it (side effect), then return the captured value.
        value = _evaluate_expression(op.value, symtab, None)
        _store(symtab, op.name, value)
        return value
    if isinstance(op, CompositionCallNode):
        return _composition_call_value(op, symtab)
    raise _RuntimeError(
        f"Can't extract a value from {type(op).__name__} as a last operation."
    )


# ---------------------------------------------------------------------------
# Condition evaluation (used inside `filter`)
# ---------------------------------------------------------------------------


def _eval_condition(
    cond: ASTNode,
    current_item: Any,
    symtab: dict[str, SymbolEntry],
) -> bool:
    if isinstance(cond, CompoundConditionNode):
        l = _eval_condition(cond.left, current_item, symtab)
        if cond.connector == "and":
            return bool(l) and bool(_eval_condition(cond.right, current_item, symtab))
        return bool(l) or bool(_eval_condition(cond.right, current_item, symtab))
    if isinstance(cond, ConditionNode):
        field_val = _eval_field(cond.field, current_item, symtab)
        if cond.op == "within":
            # Issue #19: |field - target| <= tolerance.
            tolerance = _eval_value(cond.value, current_item, symtab)
            target = _eval_value(cond.value2, current_item, symtab)
            return _within_tolerance(field_val, tolerance, target)
        value_val = _eval_value(cond.value, current_item, symtab)
        return _apply_op(cond.op, field_val, value_val)
    raise _RuntimeError(f"Can't evaluate condition {type(cond).__name__}.")


def _within_tolerance(field_val: Any, tolerance: Any, target: Any) -> bool:
    """Issue #19 — numeric tolerance comparison: True when
    |field_val - target| <= tolerance. All three operands must be numbers;
    a non-number produces a friendly runtime error rather than a Python
    TypeError."""
    for label, v in (("value", field_val), ("amount", tolerance), ("target", target)):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise _RuntimeError(
                f"'within' compares numbers, but the {label} is "
                f"{_format_scalar(v)}."
            )
    return abs(field_val - target) <= tolerance


def _eval_field(field_node: ASTNode, current_item: Any, symtab) -> Any:
    if isinstance(field_node, EachPronoun):
        return current_item
    if isinstance(field_node, NameRef):
        if isinstance(current_item, dict) and field_node.name in current_item:
            return current_item[field_node.name]
        if field_node.name in symtab:
            val = symtab[field_node.name].value
            if isinstance(val, DecayingValue):
                return val.current_value
            return val
        raise _RuntimeError(
            f"I can't find '{field_node.name}' in this item."
        )
    if isinstance(field_node, FieldAccessNode):
        # v2b §77 / v2d §100 — `<field> of <record>` on the left side of
        # a condition. Read live from the named record at compare time;
        # the analyzer has already verified record existence + field.
        record = symtab[field_node.record_name].value
        return record[field_node.field]
    raise _RuntimeError(f"Unexpected field reference {type(field_node).__name__}.")


def _eval_value(value_node: ASTNode, current_item: Any, symtab) -> Any:
    if isinstance(value_node, NumberLiteral):
        return value_node.value
    if isinstance(value_node, BareWord):
        if value_node.word in symtab:
            val = symtab[value_node.word].value
            if isinstance(val, DecayingValue):
                return val.current_value
            return val
        return value_node.word
    if isinstance(value_node, QuotedString):
        # v2c §86/§87 — quoted value is always a literal string.
        return value_node.content
    if isinstance(value_node, EachPronoun):
        return current_item
    if isinstance(value_node, FieldAccessNode):
        # v2b §77: `where ... is <op> <field> of <record>` reads the
        # field's current value from the named record at compare time.
        record = symtab[value_node.record_name].value
        return record[value_node.field]
    if isinstance(value_node, ArithmeticNode):
        # Infrastructure Era — arithmetic on the right-hand side of a
        # comparison evaluates to a number at compare time.
        return _eval_arithmetic(value_node, symtab, current_item)
    raise _RuntimeError(f"Unexpected value {type(value_node).__name__}.")


def _eval_arithmetic(
    node: ArithmeticNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> int | float:
    """Infrastructure Era — evaluate a binary arithmetic expression.

    Operands are resolved via `_evaluate_expression` so all value AST
    shapes (literals, names, field access, BareWord, nested arithmetic)
    work uniformly. Runtime numeric guards produce friendly errors when
    an operand resolves to a non-number. Division by zero is caught and
    reported as a runtime error rather than a Python exception.

    Result type: integer when both operands are integers and the
    operation preserves integer-ness (plus, minus, multiplied_by); for
    divided_by the result is an int when it divides evenly, else float.
    """
    left = _eval_arithmetic_operand(node.left, symtab, current_item)
    right = _eval_arithmetic_operand(node.right, symtab, current_item)
    if isinstance(left, bool) or not isinstance(left, (int, float)):
        raise _RuntimeError(
            f"I can only do arithmetic with numbers, but the left side "
            f"of '{_OP_PROSE[node.op]}' is {_format_scalar(left)}."
        )
    if isinstance(right, bool) or not isinstance(right, (int, float)):
        raise _RuntimeError(
            f"I can only do arithmetic with numbers, but the right side "
            f"of '{_OP_PROSE[node.op]}' is {_format_scalar(right)}."
        )
    if node.op == "plus":
        return left + right
    if node.op == "minus":
        return left - right
    if node.op == "multiplied_by":
        return left * right
    if node.op == "divided_by":
        if right == 0:
            raise _RuntimeError("I can't divide by zero.")
        result = left / right
        if isinstance(result, float) and result.is_integer():
            return int(result)
        return result
    raise _RuntimeError(f"Unknown arithmetic operator '{node.op}'.")


def _eval_arithmetic_operand(
    operand: ASTNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any,
) -> Any:
    """Resolve an arithmetic operand with iterator-context awareness.

    A BareWord inside `each <list-of-records>` resolves to the field on
    the current record when present — mirroring the iterator-first
    resolution that `_exec_add` uses for its item slot. Everything else
    delegates to `_evaluate_expression`.
    """
    if (
        isinstance(operand, BareWord)
        and isinstance(current_item, dict)
        and operand.word in current_item
    ):
        return current_item[operand.word]
    return _evaluate_expression(operand, symtab, current_item)


_OP_PROSE = {
    "plus": "plus",
    "minus": "minus",
    "multiplied_by": "multiplied by",
    "divided_by": "divided by",
}


def _apply_op(op: str, a: Any, b: Any) -> bool:
    # NOTE: this function is duplicated in listener.py to avoid a circular
    # import between interpreter and listener. Both copies must stay in
    # sync when adding new operators.
    if op == "is":
        return a == b
    if op == "above":
        return a > b
    if op == "below":
        return a < b
    if op == "equal_to":
        return a == b
    if op == "not_above":
        return not (a > b)   # ≤
    if op == "not_below":
        return not (a < b)   # ≥
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
    raise _RuntimeError(f"Unknown comparison operator '{op}'.")


# ---------------------------------------------------------------------------
# Symbol-table storage with type inference + copy semantics
# ---------------------------------------------------------------------------


def _store(
    symtab: dict[str, SymbolEntry],
    name: str,
    value: Any,
    *,
    source_names: list[str | None] | None = None,
    descriptor: str | None = None,
) -> None:
    """Store value under name. Existing entries are overwritten (v1d §58).
    Copy-on-store enforces v1's copy semantics (§24 line 486).

    `source_names` (U2) carries the names of the records the list was
    built from, when applicable, so schema-mismatch errors can name the
    offender. None for all non-list-of-records cases.

    `descriptor` is the user-written word between article and `called`
    (e.g. `source` in `remember a source called readme`). Only the
    `remember` exec paths pass this; interpreter-internal stores
    (gather, pack verb writes, add) leave it None.

    Metabolic Era batch 1: if the existing entry's value is a
    DecayingValue and the new value is numeric, this is a
    reinforcement — reset ticks_elapsed and replace initial_value
    while preserving the period. A non-numeric overwrite discards
    the decay wrapper entirely.
    """
    existing = symtab.get(name)
    if (
        existing is not None
        and isinstance(existing.value, DecayingValue)
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
    ):
        existing.value.reinforce(float(value))
        return
    value = copy.deepcopy(value)
    type_, schema = _infer_type_and_schema(value)
    symtab[name] = SymbolEntry(
        name=name, value=value, type=type_, schema=schema,
        source_names=source_names, descriptor=descriptor,
    )


def _infer_type_and_schema(v: Any) -> tuple[str, dict[str, str] | None]:
    if isinstance(v, DecayingValue):
        return "number", None
    if isinstance(v, bool):
        return "number", None  # v1 has no bools; defensive
    if isinstance(v, (int, float)):
        return "number", None
    if isinstance(v, str):
        return "string", None
    if isinstance(v, dict):
        return "record", {k: _scalar_type(val) for k, val in v.items()}
    if isinstance(v, list):
        if not v:
            # Default empty lists to numbers; v1 doesn't define a
            # canonical "empty list type" — analyzer would have rejected
            # construction of an empty list anyway.
            return "list_of_numbers", None
        first = v[0]
        if isinstance(first, dict):
            return "list_of_records", None
        if isinstance(first, str):
            return "list_of_strings", None
        return "list_of_numbers", None
    return "unknown", None


def _scalar_type(v: Any) -> str:
    if isinstance(v, bool):
        return "number"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, dict):
        return "record"
    return "unknown"


# ---------------------------------------------------------------------------
# Display formats (v1b §42)
# ---------------------------------------------------------------------------


def _display_lines(v: Any) -> list[str]:
    """Format a value as output lines per v1b §42."""
    if isinstance(v, DecayingValue):
        return [_format_scalar(v.current_value)]
    if isinstance(v, list) and v and isinstance(v[0], dict):
        # List of records: one record per line.
        return [_format_record(r) for r in v]
    if isinstance(v, list):
        return [", ".join(_format_scalar(item) for item in v)]
    if isinstance(v, dict):
        return [_format_record(v)]
    return [_format_scalar(v)]


def _format_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v.is_integer():
            return str(int(v))
        return str(v)
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return _format_record(v)
    return str(v)


def _format_record(r: dict[str, Any]) -> str:
    return ", ".join(f"{k}: {_format_scalar(val)}" for k, val in r.items())

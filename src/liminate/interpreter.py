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
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from .adapter import LiveValueRegistry
from .analyzer import SymbolEntry, analyze


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
    ASTNode,
    BareWord,
    ChooseBranch,
    ChooseNode,
    CombineNode,
    CompositionCallNode,
    CompoundConditionNode,
    ConditionNode,
    CountNode,
    EachNode,
    EachPronoun,
    FieldAccessNode,
    FilterNode,
    FinishNode,
    GatherNode,
    KeepNode,
    NameRef,
    NumberLiteral,
    PackVerbNode,
    QuotedString,
    RememberCompositionNode,
    RememberListNode,
    RememberRecordNode,
    RememberValueNode,
    SequenceNode,
    ShowNode,
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
    _mark_live_value_active_if_remember(node, live_value_registry)
    return LiminateResult(
        status=ResultStatus.SUCCESS,
        canonical=render(node),
        output=output if output else None,
        executed=True,
    )


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
    return LiminateResult(
        status=ResultStatus.ERROR_SEMANTIC,
        canonical=render(seq),
        output=outputs if outputs else None,
        message=msg,
        executed=False,
    )


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
    _store(symtab, node.name, value)
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
    """Dispatch a pack-defined verb by its execution type.

    v4a defines exactly one execution type — `set_value` — which writes
    the source slot's resolved name into a symbol named `target_name`.
    The analyzer has already validated slot values and type constraints,
    so the dispatch can assume well-formed inputs.
    """
    execution = node.signature.execution
    if execution.type == "set_value":
        slot_name = execution.source_slot
        target_name = execution.target_name
        if slot_name is None or target_name is None:
            raise _RuntimeError(
                f"Pack verb '{node.word}' has an incomplete set_value "
                f"execution definition."
            )
        value_node = node.slot_values.get(slot_name)
        if value_node is None:
            raise _RuntimeError(
                f"Pack verb '{node.word}' is missing its '{slot_name}' slot."
            )
        if isinstance(value_node, NameRef):
            value: Any = value_node.name
        else:
            value = _evaluate_expression(value_node, symtab, None)
        _store(symtab, target_name, value)
        return []
    raise _RuntimeError(
        f"Pack verb '{node.word}' uses unknown execution type "
        f"'{execution.type}'."
    )


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
        return [_format_scalar(record[name])]
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
            return copy.deepcopy(symtab[expr.word].value)
        return expr.word
    if isinstance(expr, QuotedString):
        # v2c §86/§87 — quoted content is always a literal string. No
        # symbol-table fallback (unlike BareWord) — quotes mark data.
        return expr.content
    if isinstance(expr, NameRef):
        if expr.name in symtab:
            return copy.deepcopy(symtab[expr.name].value)
        raise _RuntimeError(
            f"I can't find '{expr.name}'. You might need to 'remember' it first."
        )
    if isinstance(expr, EachPronoun):
        return current_item
    if isinstance(expr, FieldAccessNode):
        # v2b §77: extract <field> of <record> as a value.
        record = symtab[expr.record_name].value
        return copy.deepcopy(record[expr.field])
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
        value_val = _eval_value(cond.value, current_item, symtab)
        return _apply_op(cond.op, field_val, value_val)
    raise _RuntimeError(f"Can't evaluate condition {type(cond).__name__}.")


def _eval_field(field_node: ASTNode, current_item: Any, symtab) -> Any:
    if isinstance(field_node, EachPronoun):
        return current_item
    if isinstance(field_node, NameRef):
        if isinstance(current_item, dict) and field_node.name in current_item:
            return current_item[field_node.name]
        if field_node.name in symtab:
            return symtab[field_node.name].value
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
            return symtab[value_node.word].value
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
    raise _RuntimeError(f"Unexpected value {type(value_node).__name__}.")


def _apply_op(op: str, a: Any, b: Any) -> bool:
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
) -> None:
    """Store value under name. Existing entries are overwritten (v1d §58).
    Copy-on-store enforces v1's copy semantics (§24 line 486).

    `source_names` (U2) carries the names of the records the list was
    built from, when applicable, so schema-mismatch errors can name the
    offender. None for all non-list-of-records cases.
    """
    value = copy.deepcopy(value)
    type_, schema = _infer_type_and_schema(value)
    symtab[name] = SymbolEntry(
        name=name, value=value, type=type_, schema=schema,
        source_names=source_names,
    )


def _infer_type_and_schema(v: Any) -> tuple[str, dict[str, str] | None]:
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

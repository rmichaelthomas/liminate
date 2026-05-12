"""Interpreter for Inscript v1.

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

This module performs both the per-op analyze gate and execution. The
analyzer is re-invoked per operation inside SequenceNode bodies and
composition bodies so that mid-sequence failures honor stepwise
semantics (v1d §56).
"""

from __future__ import annotations

import copy
from typing import Any

from .analyzer import SymbolEntry, analyze
from .parser import (
    ASTNode,
    BareWord,
    CombineNode,
    CompositionCallNode,
    CompoundConditionNode,
    ConditionNode,
    CountNode,
    EachNode,
    EachPronoun,
    FilterNode,
    GatherNode,
    KeepNode,
    NameRef,
    NumberLiteral,
    RememberCompositionNode,
    RememberListNode,
    RememberRecordNode,
    RememberValueNode,
    SequenceNode,
    ShowNode,
)
from .renderer import render
from .result import InscriptResult, ResultStatus


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def execute(
    ast: ASTNode,
    symbol_table: dict[str, SymbolEntry],
) -> InscriptResult:
    """Execute a single top-level AST against a mutable symbol table.

    Returns an InscriptResult. For SequenceNode the interpreter loops
    per-op so that earlier successes commit even if a later op fails
    (v1d §56).
    """
    if isinstance(ast, SequenceNode):
        return _execute_sequence(ast, symbol_table)
    return _execute_single(ast, symbol_table)


# ---------------------------------------------------------------------------
# Per-op execution
# ---------------------------------------------------------------------------


class _RuntimeError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _execute_single(
    node: ASTNode,
    symtab: dict[str, SymbolEntry],
    current_item: Any = None,
) -> InscriptResult:
    analysis = analyze(node, symtab)
    if isinstance(analysis, InscriptResult):
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
        return InscriptResult(
            status=ResultStatus.ERROR_SEMANTIC,
            canonical=render(node),
            message=e.message,
            executed=False,
        )
    return InscriptResult(
        status=ResultStatus.SUCCESS,
        canonical=render(node),
        output=output if output else None,
        executed=True,
    )


def _execute_sequence(
    seq: SequenceNode,
    symtab: dict[str, SymbolEntry],
) -> InscriptResult:
    completed_canonicals: list[str] = []
    outputs: list[str] = []
    for op in seq.operations:
        analysis = analyze(op, symtab)
        if isinstance(analysis, InscriptResult):
            return _stepwise_error(op, analysis, completed_canonicals, outputs, seq)
        try:
            op_output = _exec_op(op, symtab)
        except _RuntimeError as e:
            return _stepwise_error(
                op,
                InscriptResult(
                    status=ResultStatus.ERROR_SEMANTIC,
                    message=e.message,
                ),
                completed_canonicals,
                outputs,
                seq,
            )
        completed_canonicals.append(render(op))
        if op_output:
            outputs.extend(op_output)
    return InscriptResult(
        status=ResultStatus.SUCCESS,
        canonical=render(seq),
        output=outputs if outputs else None,
        executed=True,
    )


def _stepwise_error(
    failed_op: ASTNode,
    failure: InscriptResult,
    completed_canonicals: list[str],
    outputs: list[str],
    seq: SequenceNode,
) -> InscriptResult:
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
    return InscriptResult(
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
    if isinstance(node, CompositionCallNode):
        return _exec_composition_call(node, symtab)
    if isinstance(node, SequenceNode):
        # Nested sequence (e.g. inside a composition body).
        outputs: list[str] = []
        for op in node.operations:
            analysis = analyze(op, symtab)
            if isinstance(analysis, InscriptResult):
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
    _store(symtab, node.name, items)
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
# composition call — body executes against current symbol table (v1b §41)
# ---------------------------------------------------------------------------


def _exec_composition_call(
    node: CompositionCallNode,
    symtab: dict[str, SymbolEntry],
) -> list[str]:
    body = symtab[node.name].value
    if isinstance(body, SequenceNode):
        outputs: list[str] = []
        for op in body.operations:
            analysis = analyze(op, symtab)
            if isinstance(analysis, InscriptResult):
                raise _RuntimeError(analysis.message or "")
            out = _exec_op(op, symtab)
            if out:
                outputs.extend(out)
        return outputs
    analysis = analyze(body, symtab)
    if isinstance(analysis, InscriptResult):
        raise _RuntimeError(analysis.message or "")
    return _exec_op(body, symtab) or []


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
    if isinstance(expr, NameRef):
        if expr.name in symtab:
            return copy.deepcopy(symtab[expr.name].value)
        raise _RuntimeError(
            f"I can't find '{expr.name}'. You might need to 'remember' it first."
        )
    if isinstance(expr, EachPronoun):
        return current_item
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
        # v1 doesn't define a return value for compositions; their side
        # effects flow through the shared symbol table. Treat the call's
        # display output as its "result" would over-reach the spec.
        raise _RuntimeError(
            "Composition calls can't be used as a value in this version."
        )
    raise _RuntimeError(f"Can't evaluate {type(expr).__name__} as a value.")


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
    raise _RuntimeError(f"Unexpected field reference {type(field_node).__name__}.")


def _eval_value(value_node: ASTNode, current_item: Any, symtab) -> Any:
    if isinstance(value_node, NumberLiteral):
        return value_node.value
    if isinstance(value_node, BareWord):
        if value_node.word in symtab:
            return symtab[value_node.word].value
        return value_node.word
    if isinstance(value_node, EachPronoun):
        return current_item
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


def _store(symtab: dict[str, SymbolEntry], name: str, value: Any) -> None:
    """Store value under name. Existing entries are overwritten (v1d §58).
    Copy-on-store enforces v1's copy semantics (§24 line 486).
    """
    value = copy.deepcopy(value)
    type_, schema = _infer_type_and_schema(value)
    symtab[name] = SymbolEntry(
        name=name, value=value, type=type_, schema=schema,
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

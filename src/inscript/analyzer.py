"""Semantic analyzer for Inscript v1.

Sources:
- inception §23 (semantic analysis: symbol table with types, structured
  records via `as`, named composition validation split — grammar at
  definition, names at call)
- v1b §38 (`combine` numeric-only)
- v1c §49 (iterator context: temporary binding for `each`)
- v1c §50 outcome 5 (semantic errors halt before execution)
- v1c §52 (deterministic interpretation only)
- v1d §59 (homogeneous lists only)
- v1d §60 (record schema homogeneity for field operations)
- v1d §62 (descending ranges are errors)
- v1d §63 (gather range cap 10,000)
- v1d §64 (structured results — no direct I/O)

The analyzer validates a SINGLE operation AST against the symbol table.
For SequenceNode statements, the orchestrator (interpreter) iterates ops
to honor stepwise execution semantics (v1d §56) — the analyzer's
SequenceNode fallback is provided defensively but won't reflect mid-
sequence state changes. The interpreter calls analyze() per op.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
from .result import InscriptResult, ResultStatus

GATHER_RANGE_CAP = 10_000  # v1d §63


# ---------------------------------------------------------------------------
# Symbol table entry
# ---------------------------------------------------------------------------


@dataclass
class SymbolEntry:
    name: str
    value: Any
    type: str   # see _TYPE_NAMES below
    schema: dict[str, str] | None = None  # records only
    # For list_of_records: the source-record names captured at list
    # construction. Populated when the list was built via
    # `remember a list with X and Y and Z` where each item was a name
    # reference to a record. Used by U2/U3 to name the offending record
    # in schema-mismatch errors. None if the list was built another way
    # (literal values, captured from `keep`/`filter`); the analyzer falls
    # back to a positional identifier in that case.
    source_names: list[str | None] | None = None


# Recognized type strings.
_TYPE_NAMES = frozenset({
    "number", "string", "record",
    "list_of_numbers", "list_of_strings", "list_of_records",
    "composition",
})


# ---------------------------------------------------------------------------
# Iterator context (v1c §49)
# ---------------------------------------------------------------------------


@dataclass
class IteratorContext:
    collection_name: str
    # For lists of records: per-record schemas (one dict per record).
    record_schemas: list[dict[str, str]] | None = None
    # For flat lists: type of the items ("number" or "string").
    scalar_type: str | None = None


# ---------------------------------------------------------------------------
# Internal error
# ---------------------------------------------------------------------------


class _SemanticError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def analyze(
    node: ASTNode,
    symbol_table: dict[str, SymbolEntry],
    iterator: IteratorContext | None = None,
) -> ASTNode | InscriptResult:
    """Validate a single AST node.

    Returns:
        - The AST node unchanged on success.
        - InscriptResult with ERROR_SEMANTIC on failure.

    SequenceNode is validated by recursing through ops against the same
    symbol-table snapshot; the orchestrator should iterate per-op to
    honor v1d §56 stepwise execution.
    """
    try:
        if isinstance(node, SequenceNode):
            for op in node.operations:
                r = analyze(op, symbol_table, iterator)
                if isinstance(r, InscriptResult):
                    return r
            return node
        _check(node, symbol_table, iterator)
    except _SemanticError as e:
        return InscriptResult(
            status=ResultStatus.ERROR_SEMANTIC,
            message=e.message,
            executed=False,
        )
    return node


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def _check(
    node: ASTNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
) -> None:
    if isinstance(node, RememberValueNode):
        _check_remember_value(node, symtab, iterator)
    elif isinstance(node, RememberListNode):
        _check_remember_list(node, symtab)
    elif isinstance(node, RememberRecordNode):
        _check_remember_record(node, symtab)
    elif isinstance(node, RememberCompositionNode):
        pass  # §23 line 466: names checked at call time, not here.
    elif isinstance(node, ShowNode):
        _check_show(node, symtab, iterator)
    elif isinstance(node, FilterNode):
        _check_filter(node, symtab)
    elif isinstance(node, KeepNode):
        # v2a §67: same semantic checks as filter — target must be a list,
        # condition fields must resolve. No new constraint.
        _check_keep(node, symtab)
    elif isinstance(node, CountNode):
        _check_count(node, symtab)
    elif isinstance(node, GatherNode):
        _check_gather(node)
    elif isinstance(node, CombineNode):
        _check_combine(node, symtab)
    elif isinstance(node, EachNode):
        _check_each(node, symtab)
    elif isinstance(node, CompositionCallNode):
        _check_composition_call(node, symtab)
    elif isinstance(node, SequenceNode):
        for op in node.operations:
            _check(op, symtab, iterator)
    else:
        raise _SemanticError(f"unsupported AST node {type(node).__name__}")


# ---------------------------------------------------------------------------
# remember
# ---------------------------------------------------------------------------


def _check_remember_value(
    node: RememberValueNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
) -> None:
    _check_value_expr(node.value, symtab, iterator)


def _check_value_expr(
    value_node: ASTNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
) -> None:
    if isinstance(value_node, (NumberLiteral, BareWord, EachPronoun)):
        return
    if isinstance(value_node, NameRef):
        if value_node.name not in symtab:
            raise _SemanticError(
                f"I can't find '{value_node.name}'. "
                f"You might need to 'remember' it first."
            )
        return
    _check(value_node, symtab, iterator)


def _check_remember_list(
    node: RememberListNode,
    symtab: dict[str, SymbolEntry],
) -> None:
    if not node.items:
        raise _SemanticError("A list needs at least one item.")
    types: list[str] = []
    examples: list[str] = []
    for item in node.items:
        t, ex = _infer_item_type(item, symtab)
        types.append(t)
        examples.append(ex)
    distinct = set(types)
    if len(distinct) > 1:
        # v1d §59: report the first mismatch.
        first = types[0]
        first_ex = examples[0]
        for i, t in enumerate(types):
            if t != first:
                raise _SemanticError(
                    f"A list can't mix {_plural(first)} and {_plural(t)}. "
                    f"'{first_ex}' is {_singular(first)} but "
                    f"'{examples[i]}' is {_singular(t)}."
                )
    only = next(iter(distinct))
    if only not in ("number", "string", "record"):
        raise _SemanticError(
            f"v1 lists may only contain numbers, text, or records. "
            f"'{examples[0]}' is {_singular(only)}."
        )


def _infer_item_type(item: ASTNode, symtab: dict[str, SymbolEntry]) -> tuple[str, str]:
    if isinstance(item, NumberLiteral):
        return "number", _fmt_number(item.value)
    if isinstance(item, BareWord):
        if item.word in symtab:
            return symtab[item.word].type, item.word
        return "string", item.word
    raise _SemanticError(f"Unexpected list item {type(item).__name__}.")


def _check_remember_record(
    node: RememberRecordNode,
    symtab: dict[str, SymbolEntry],
) -> None:
    # Field values are single tokens (v1d §61). Validation of field
    # value types beyond "single token" is not in the v1 spec.
    if not node.fields:
        raise _SemanticError("A record needs at least one field.")


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


def _check_show(
    node: ShowNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
) -> None:
    if node.target is None:
        if iterator is None:
            raise _SemanticError("I need something to show.")
        return
    if not isinstance(node.target, NameRef):
        raise _SemanticError("Unexpected target for 'show'.")
    name = node.target.name

    # v2a §68 (D4): `show <field> of <record>` — verify the record exists,
    # is a record (not a list/scalar/composition), and contains the field.
    if node.record_name is not None:
        if node.record_name not in symtab:
            raise _SemanticError(
                f"I can't find '{node.record_name}'. "
                f"You might need to 'remember' it first."
            )
        entry = symtab[node.record_name]
        if entry.type != "record":
            # U8 (v2.1-patch): when the target is a list-of-records, the
            # user's intent is almost always "show this field for each
            # row" — guide them toward `each ... show <field>` rather
            # than the generic type-mismatch.
            if entry.type == "list_of_records":
                raise _SemanticError(
                    f"'of' needs a single record. '{node.record_name}' "
                    f"is a list of records — did you mean: "
                    f"each the {node.record_name} show {name}?"
                )
            raise _SemanticError(
                f"'of' needs a record. '{node.record_name}' is "
                f"{_singular(entry.type)}."
            )
        if entry.schema is None or name not in entry.schema:
            raise _SemanticError(
                f"'{node.record_name}' doesn't have a field called '{name}'."
            )
        return

    # Iterator-first resolution (v1c §49).
    if iterator is not None and iterator.record_schemas is not None:
        # Each field referenced (target + any v2a §69 extras) must exist
        # on every record in the iterated list.
        all_field_names = [name, *node.extra_fields]
        # U7 (v2.1-patch): reject duplicate field names in multi-field
        # `each ... show`. Two identical columns are almost certainly a
        # typo (`show class and class` instead of `show class and words`)
        # and silently accepting them leaves the user with broken-looking
        # output. Per v1c §52 (deterministic interpretation only),
        # erroring is safer than guessing.
        seen: set[str] = set()
        for fname in all_field_names:
            if fname in seen:
                raise _SemanticError(
                    f"You listed '{fname}' twice in this show. "
                    f"Did you mean another field?"
                )
            seen.add(fname)
        for fname in all_field_names:
            in_all = all(fname in s for s in iterator.record_schemas)
            in_any = any(fname in s for s in iterator.record_schemas)
            if in_all:
                continue
            if in_any:
                raise _SemanticError(
                    _schema_mismatch_message(
                        symtab[iterator.collection_name],
                        iterator.record_schemas,
                        fname,
                    )
                )
            # If we're iterating records and the name matches nothing,
            # fall through to symbol-table lookup only for the *first*
            # field (target) — extras are only legal as record fields.
            if fname != name:
                raise _SemanticError(
                    _schema_mismatch_message(
                        symtab[iterator.collection_name],
                        iterator.record_schemas,
                        fname,
                    )
                )
        if all(name in s for s in iterator.record_schemas):
            return
        # Field missing from every record — fall through to symbol-table lookup.
    elif node.extra_fields:
        # v2a §69 (D1): multi-field show only makes sense over a list of
        # records. Reject the construct on flat lists / outside of each.
        raise _SemanticError(
            "Multiple fields in 'show' only work inside an 'each' loop "
            "over a list of records."
        )
    if name in symtab:
        return
    raise _SemanticError(
        f"I can't find '{name}'. You might need to 'remember' it first."
    )


# ---------------------------------------------------------------------------
# filter
# ---------------------------------------------------------------------------


def _check_filter(node: FilterNode, symtab: dict[str, SymbolEntry]) -> None:
    name = node.target.name
    entry = _require_list(name, symtab, verb="filter")
    iterator = _make_iterator(name, entry)
    _check_condition(node.condition, symtab, iterator)


def _check_keep(node: KeepNode, symtab: dict[str, SymbolEntry]) -> None:
    """v2a §67. Validation mirrors filter — only execution semantics differ."""
    name = node.target.name
    entry = _require_list(name, symtab, verb="keep")
    iterator = _make_iterator(name, entry)
    _check_condition(node.condition, symtab, iterator)


def _check_condition(
    cond: ASTNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext,
) -> None:
    if isinstance(cond, CompoundConditionNode):
        _check_condition(cond.left, symtab, iterator)
        _check_condition(cond.right, symtab, iterator)
        return
    if not isinstance(cond, ConditionNode):
        raise _SemanticError("Unexpected condition shape.")

    field_type, field_label = _resolve_field(cond.field, symtab, iterator)
    value_type, value_label = _resolve_value(cond.value, symtab, iterator)

    if cond.op == "is":
        # Equality — types should agree for a sensible comparison.
        # No type-error fires here for v1 (the spec doesn't lock one).
        return
    if cond.op in ("above", "below"):
        _require_numeric(field_type, field_label, cond.op)
        _require_numeric(value_type, value_label, cond.op)
        return
    if cond.op == "equal_to":
        return  # any same-type comparison; analyzer doesn't enforce
    if cond.op.startswith("not_"):
        inner = cond.op[len("not_"):]
        if inner in ("above", "below"):
            _require_numeric(field_type, field_label, f"not {inner}")
            _require_numeric(value_type, value_label, f"not {inner}")
        return
    raise _SemanticError(f"Unknown comparison operator '{cond.op}'.")


def _require_numeric(t: str, label: str, op: str) -> None:
    if t == "number":
        return
    raise _SemanticError(
        f"'{op}' requires numbers, but '{label}' is {_singular(t)}."
    )


def _schema_mismatch_message(
    entry: SymbolEntry,
    schemas: list[dict[str, str]],
    field_name: str,
) -> str:
    """Build the schema-homogeneity error for a list of records.

    U2: name the first offending record (by source name when known,
    else by position). U3: distinguish the zero-match case ("No item
    has it") from the partial case ("'X' doesn't have it; others do").
    """
    in_any = any(field_name in s for s in schemas)
    if not in_any:
        return f"No item in '{entry.name}' has a field called '{field_name}'."
    missing_idx = next(
        i for i, s in enumerate(schemas) if field_name not in s
    )
    if entry.source_names and missing_idx < len(entry.source_names):
        src = entry.source_names[missing_idx]
        if src:
            offender = f"'{src}' in '{entry.name}'"
        else:
            offender = f"Item {missing_idx + 1} in '{entry.name}'"
    else:
        offender = f"Item {missing_idx + 1} in '{entry.name}'"
    return (
        f"{offender} doesn't have a field called '{field_name}'. "
        f"Other items do have it."
    )


def _resolve_field(
    field_node: ASTNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext,
) -> tuple[str, str]:
    if isinstance(field_node, EachPronoun):
        if iterator.record_schemas is not None:
            return "record", "each"
        return iterator.scalar_type or "unknown", "each"
    if isinstance(field_node, NameRef):
        name = field_node.name
        if iterator.record_schemas is not None:
            in_all = all(name in s for s in iterator.record_schemas)
            if in_all:
                # Determine the common type of this field.
                types = {s[name] for s in iterator.record_schemas}
                return (next(iter(types)) if len(types) == 1 else "mixed"), name
            raise _SemanticError(
                _schema_mismatch_message(
                    symtab[iterator.collection_name],
                    iterator.record_schemas,
                    name,
                )
            )
        # Scalar list — fields don't exist; user must use `each`.
        raise _SemanticError(
            f"In a list of {_plural(iterator.scalar_type or 'items')}, "
            f"use 'each' to refer to the current item."
        )
    raise _SemanticError("Unexpected field reference.")


def _resolve_value(
    value_node: ASTNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext,
) -> tuple[str, str]:
    if isinstance(value_node, NumberLiteral):
        return "number", _fmt_number(value_node.value)
    if isinstance(value_node, BareWord):
        if value_node.word in symtab:
            entry = symtab[value_node.word]
            return entry.type, value_node.word
        return "string", value_node.word
    if isinstance(value_node, EachPronoun):
        if iterator.record_schemas is not None:
            return "record", "each"
        return iterator.scalar_type or "unknown", "each"
    raise _SemanticError("Unexpected value in condition.")


# ---------------------------------------------------------------------------
# count, combine, gather, each
# ---------------------------------------------------------------------------


def _check_count(node: CountNode, symtab: dict[str, SymbolEntry]) -> None:
    _require_list(node.target.name, symtab, verb="count")


def _check_combine(node: CombineNode, symtab: dict[str, SymbolEntry]) -> None:
    name = node.target.name
    if name not in symtab:
        raise _SemanticError(
            f"I can't find '{name}'. You might need to 'remember' it first."
        )
    entry = symtab[name]
    if entry.type == "list_of_numbers":
        return
    if entry.type == "list_of_strings":
        raise _SemanticError(f"I can only combine numbers. '{name}' contains text.")
    if entry.type == "list_of_records":
        raise _SemanticError(f"I can only combine numbers. '{name}' contains records.")
    raise _SemanticError(
        f"I can only combine numbers. '{name}' is {_singular(entry.type)}."
    )


def _check_gather(node: GatherNode) -> None:
    if node.from_val > node.to_val:
        raise _SemanticError(
            f"The 'from' value ({_fmt_number(node.from_val)}) must be less "
            f"than or equal to the 'to' value ({_fmt_number(node.to_val)}). "
            f"Try: gather the {node.name} from {_fmt_number(node.to_val)} "
            f"to {_fmt_number(node.from_val)}."
        )
    # Range size = to - from + 1 (inclusive).
    size = node.to_val - node.from_val + 1
    if size > GATHER_RANGE_CAP:
        raise _SemanticError(
            f"That range is too large. The maximum is "
            f"{GATHER_RANGE_CAP:,} items."
        )


def _check_each(node: EachNode, symtab: dict[str, SymbolEntry]) -> None:
    name = node.collection.name
    entry = _require_list(name, symtab, verb="iterate over")
    iterator = _make_iterator(name, entry)
    _check(node.action, symtab, iterator)


# ---------------------------------------------------------------------------
# named-composition call (§23 line 466 / v1b §41)
# ---------------------------------------------------------------------------


def _check_composition_call(
    node: CompositionCallNode,
    symtab: dict[str, SymbolEntry],
) -> None:
    if node.name not in symtab or symtab[node.name].type != "composition":
        raise _SemanticError(f"I can't find a composition called '{node.name}'.")
    body = symtab[node.name].value
    # §23: name resolution at call time. Analyze the body now.
    _check(body, symtab, iterator=None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_list(
    name: str,
    symtab: dict[str, SymbolEntry],
    *,
    verb: str,
) -> SymbolEntry:
    if name not in symtab:
        raise _SemanticError(
            f"I can't find '{name}'. You might need to 'remember' it first."
        )
    entry = symtab[name]
    if entry.type not in ("list_of_numbers", "list_of_strings", "list_of_records"):
        if verb == "filter":
            msg = f"I can only filter a list. '{name}' is {_singular(entry.type)}."
        elif verb == "keep":
            # v2a §67: error path for keep on a non-list mirrors filter.
            msg = f"I can only keep from a list. '{name}' is {_singular(entry.type)}."
        elif verb == "count":
            msg = f"I can only count a list. '{name}' is {_singular(entry.type)}."
        elif verb == "iterate over":
            msg = f"I can only iterate over a list. '{name}' is {_singular(entry.type)}."
        else:
            msg = f"I expected a list for '{verb}'. '{name}' is {_singular(entry.type)}."
        raise _SemanticError(msg)
    return entry


def _make_iterator(name: str, entry: SymbolEntry) -> IteratorContext:
    if entry.type == "list_of_records":
        schemas: list[dict[str, str]] = []
        for record in entry.value:
            schemas.append({k: _value_type(v) for k, v in record.items()})
        return IteratorContext(collection_name=name, record_schemas=schemas)
    if entry.type == "list_of_numbers":
        return IteratorContext(collection_name=name, scalar_type="number")
    if entry.type == "list_of_strings":
        return IteratorContext(collection_name=name, scalar_type="string")
    raise _SemanticError(f"'{name}' isn't a list I can iterate.")


def _value_type(v: Any) -> str:
    if isinstance(v, bool):
        # v1 has no booleans; defensive only.
        return "number"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, dict):
        return "record"
    return "unknown"


_SINGULAR = {
    "number": "a number",
    "string": "text",
    "record": "a record",
    "list_of_numbers": "a list of numbers",
    "list_of_strings": "a list of text",
    "list_of_records": "a list of records",
    "composition": "a composition",
    "unknown": "an unknown type",
}
_PLURAL = {
    "number": "numbers",
    "string": "text",
    "record": "records",
    "list_of_numbers": "lists of numbers",
    "list_of_strings": "lists of text",
    "list_of_records": "lists of records",
}


def _singular(t: str) -> str:
    return _SINGULAR.get(t, t)


def _plural(t: str) -> str:
    return _PLURAL.get(t, t)


def _fmt_number(v: int | float) -> str:
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return str(v)
    if v.is_integer():
        return str(int(v))
    return str(v)

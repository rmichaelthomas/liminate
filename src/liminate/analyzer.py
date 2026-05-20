"""Semantic analyzer for Liminate v1 / v2a / v2b / v2c / v2d / v3a.

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
- v3a §108 (when condition/guard validation at registration time)
- v3a §111 (action-block live-value ownership rules)
- v3a §112 (finish is action-block-only — Phase 1 calls are errors)
- v3a §117 (live values are adapter-owned after Phase 2 begins)

The analyzer validates a SINGLE operation AST against the symbol table.
For SequenceNode statements, the orchestrator (interpreter) iterates ops
to honor stepwise execution semantics (v1d §56) — the analyzer's
SequenceNode fallback is provided defensively but won't reflect mid-
sequence state changes. The interpreter calls analyze() per op.

v3a adds two optional analyze() parameters that carry listener-mode
context:
- `in_action_block` — True when the statement is being analyzed at
  handler firing time. Controls FinishNode legality (§112) and the
  live-value `remember`-overwrite check (§111/§117).
- `live_value_names` — names declared by domain packs as live values.
  `remember` on these inside action blocks is rejected (§111/§117);
  `filter` on these is rejected in all contexts because `filter` is
  destructive (§111).

Action blocks themselves are NOT analyzed at WhenNode-registration time
(§108): per the spec, "Name resolution within action blocks occurs at
firing time, not at registration time, because actions may reference
values created by other handlers or adapter updates." The registration-
time check validates only the condition and unless guard.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .parser import (
    AddNode,
    ArithmeticNode,
    AssignNode,
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
    ExpectNode,
    FieldAccessNode,
    FilterNode,
    FinishNode,
    GatherNode,
    KeepNode,
    NameRef,
    NumberLiteral,
    PackVerbNode,
    RemoveNode,
    QuotedString,
    RememberCompositionNode,
    RememberListNode,
    RememberRecordNode,
    RememberValueNode,
    RequireNode,
    SequenceNode,
    ShowNode,
    WeakensNode,
    WhenNode,
)
from .result import LiminateResult, ResultStatus
from .vocabulary import (
    AppendToListExecution,
    CompareValuesExecution,
    NumericExtractCompareExecution,
    SetFieldExecution,
    SetValueExecution,
    SubstringCheckExecution,
)

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
    # v4a §137: the descriptor word the user wrote between article and
    # `called` at definition time (e.g. "screen" in `remember a screen
    # called dashboard ...`). Preserved so pack verb type constraints can
    # check it (§135 — `navigate to` expects a record whose descriptor is
    # `screen`). None when no descriptor was written or when the entry is
    # not user-defined.
    descriptor: str | None = None
    # For list_of_records: the source-record names captured at list
    # construction. Populated when the list was built via
    # `remember a list with X and Y and Z` where each item was a name
    # reference to a record. Used by U2/U3 to name the offending record
    # in schema-mismatch errors. None if the list was built another way
    # (literal values, captured from `keep`/`filter`); the analyzer falls
    # back to a positional identifier in that case.
    source_names: list[str | None] | None = None
    # v2d §96: for compositions, the name of the single declared
    # parameter (or None if the composition takes no input). Populated
    # at definition time so the call-site mismatch check (§97) can
    # determine whether an arg was expected.
    composition_param: str | None = None


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
    *,
    in_action_block: bool = False,
    live_value_names: set[str] | None = None,
) -> ASTNode | LiminateResult:
    """Validate a single AST node.

    Returns:
        - The AST node unchanged on success.
        - LiminateResult with ERROR_SEMANTIC on failure.

    SequenceNode is validated by recursing through ops against the same
    symbol-table snapshot; the orchestrator should iterate per-op to
    honor v1d §56 stepwise execution.

    v3a parameters:
    - `in_action_block`: True when analyzing a statement inside a `when`
      action block (firing-time analysis). Affects FinishNode legality
      and the live-value `remember`-overwrite check.
    - `live_value_names`: names declared by domain packs as live values.
      None or an empty set disables live-value checks (Phase 1 sequential
      analysis before any pack is registered).
    """
    live_value_names = live_value_names or set()
    try:
        if isinstance(node, SequenceNode):
            for op in node.operations:
                r = analyze(
                    op, symbol_table, iterator,
                    in_action_block=in_action_block,
                    live_value_names=live_value_names,
                )
                if isinstance(r, LiminateResult):
                    return r
            return node
        _check(
            node, symbol_table, iterator,
            in_action_block=in_action_block,
            live_value_names=live_value_names,
        )
    except _SemanticError as e:
        return LiminateResult(
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
    *,
    in_action_block: bool = False,
    live_value_names: set[str] | None = None,
) -> None:
    live_value_names = live_value_names or set()
    if isinstance(node, RememberValueNode):
        _check_remember_value(
            node, symtab, iterator,
            in_action_block=in_action_block,
            live_value_names=live_value_names,
        )
    elif isinstance(node, RememberListNode):
        _check_remember_list(
            node, symtab,
            in_action_block=in_action_block,
            live_value_names=live_value_names,
        )
    elif isinstance(node, RememberRecordNode):
        _check_remember_record(
            node, symtab,
            in_action_block=in_action_block,
            live_value_names=live_value_names,
        )
    elif isinstance(node, RememberCompositionNode):
        pass  # §23 line 466: names checked at call time, not here.
    elif isinstance(node, ShowNode):
        _check_show(node, symtab, iterator)
    elif isinstance(node, FilterNode):
        _check_filter(node, symtab, live_value_names=live_value_names)
    elif isinstance(node, KeepNode):
        # v2a §67: same semantic checks as filter — target must be a list,
        # condition fields must resolve. v3a §111: `keep` on live values
        # is non-destructive and remains legal in all contexts.
        _check_keep(node, symtab)
    elif isinstance(node, CountNode):
        _check_count(node, symtab)
    elif isinstance(node, GatherNode):
        _check_gather(node)
    elif isinstance(node, CombineNode):
        _check_combine(node, symtab)
    elif isinstance(node, EachNode):
        _check_each(
            node, symtab,
            in_action_block=in_action_block,
            live_value_names=live_value_names,
        )
    elif isinstance(node, ChooseNode):
        # v2d §99–§102 — branch-by-branch validation with no iterator
        # context (choose has no iterator). Nested control flow inside
        # branches inherits the caller's iterator if any (e.g. choose
        # inside an each body is rejected at parse time, so this is
        # the no-iterator path in practice).
        _check_choose(
            node, symtab, iterator,
            in_action_block=in_action_block,
            live_value_names=live_value_names,
        )
    elif isinstance(node, CompositionCallNode):
        _check_composition_call(
            node, symtab,
            in_action_block=in_action_block,
            live_value_names=live_value_names,
        )
    elif isinstance(node, WhenNode):
        # v3a §108/§109: validate condition + unless at registration
        # time. The action block itself is not analyzed here — name
        # resolution within actions is deferred to firing time (§111).
        _check_when(node, symtab)
    elif isinstance(node, PackVerbNode):
        # v4a §137 + v2 (pack verb contract extension) — type-constraint
        # checking per slot, plus execution-specific checks.
        _check_pack_verb(
            node, symtab, iterator,
            live_value_names=live_value_names,
        )
    elif isinstance(node, AddNode):
        _check_add(
            node, symtab, iterator,
            live_value_names=live_value_names,
        )
    elif isinstance(node, RemoveNode):
        _check_remove(
            node, symtab, iterator,
            live_value_names=live_value_names,
        )
    elif isinstance(node, WeakensNode):
        _check_weakens(node, symtab, live_value_names=live_value_names)
    elif isinstance(node, RequireNode):
        # Normative Era batch 2 — the condition follows the same
        # validation path as `choose if`: no iterator, names resolve
        # against the symbol table directly, field access uses `of`.
        _check_choose_condition(node.condition, symtab)
    elif isinstance(node, ExpectNode):
        # Epistemic Era batch 3 — same condition validation as `require`.
        # Behavior differs only at runtime (divergence emits output;
        # never halts).
        _check_choose_condition(node.condition, symtab)
    elif isinstance(node, AssignNode):
        _check_assign(
            node, symtab, iterator,
            in_action_block=in_action_block,
            live_value_names=live_value_names,
        )
    elif isinstance(node, FinishNode):
        # v3a §112: `finish` is legal only inside a `when` action block
        # (directly, in a `choose` branch, or in a composition called
        # from one). Phase 1 sequential `finish` calls are semantic
        # errors at the call site.
        _check_finish(node, in_action_block=in_action_block)
    elif isinstance(node, SequenceNode):
        for op in node.operations:
            _check(
                op, symtab, iterator,
                in_action_block=in_action_block,
                live_value_names=live_value_names,
            )
    else:
        raise _SemanticError(f"unsupported AST node {type(node).__name__}")


# ---------------------------------------------------------------------------
# remember
# ---------------------------------------------------------------------------


def _check_remember_value(
    node: RememberValueNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
    *,
    in_action_block: bool = False,
    live_value_names: set[str] | None = None,
) -> None:
    _check_live_value_remember(node.name, in_action_block, live_value_names)
    _check_value_expr(
        node.value, symtab, iterator,
        in_action_block=in_action_block,
        live_value_names=live_value_names,
    )


def _check_live_value_remember(
    name: str,
    in_action_block: bool,
    live_value_names: set[str] | None,
) -> None:
    """v3a §111/§117 — live values are adapter-owned after Phase 2
    begins. `remember <name> with ...` inside an action block is a
    semantic error when `<name>` was declared by a domain pack as a
    live value. Phase 1 sequential `remember` is OK (it provides the
    initial value before adapters dispatch)."""
    if not in_action_block:
        return
    names = live_value_names or set()
    if name in names:
        raise _SemanticError(
            f"'{name}' is a live value provided by the domain pack and "
            f"cannot be overwritten during listener mode."
        )


def _check_value_expr(
    value_node: ASTNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
    *,
    in_action_block: bool = False,
    live_value_names: set[str] | None = None,
) -> None:
    if isinstance(value_node, (NumberLiteral, BareWord, EachPronoun, QuotedString)):
        return
    if isinstance(value_node, NameRef):
        if value_node.name not in symtab:
            raise _SemanticError(
                f"I can't find '{value_node.name}'. "
                f"You might need to 'remember' it first."
            )
        return
    if isinstance(value_node, FieldAccessNode):
        _check_field_access(value_node, symtab)
        return
    if isinstance(value_node, ArithmeticNode):
        _check_arithmetic(value_node, symtab, iterator)
        return
    if isinstance(value_node, CompositionCallNode):
        # v2b §76 — composition call in value position. v2d §97 extends
        # this with parameter-mismatch checks at the call site, before
        # body analysis runs. v3a: the void-result check is done before
        # body analysis so a structurally-mismatched call (e.g., capturing
        # the value of a composition whose body is `finish`) surfaces
        # the "doesn't return a value" framing rather than the body's
        # context-specific error.
        _check_composition_call_shape(value_node, symtab)
        verb = _composition_void_result_verb(value_node.name, symtab)
        if verb is not None:
            raise _SemanticError(
                f"Composition '{value_node.name}' doesn't return a value — "
                f"its last operation is '{verb}', which only has side effects."
            )
        _analyze_composition_body(
            value_node, symtab,
            in_action_block=in_action_block,
            live_value_names=live_value_names,
        )
        return
    _check(
        value_node, symtab, iterator,
        in_action_block=in_action_block,
        live_value_names=live_value_names,
    )


def _composition_void_result_verb(
    name: str,
    symtab: dict[str, SymbolEntry],
    visited: set[str] | None = None,
) -> str | None:
    """v2b §76 — return the verb name of a composition body's last op if
    that op is side-effect-only, else None. Resolves nested composition
    calls recursively."""
    if visited is None:
        visited = set()
    if name in visited:
        return None  # defensive: cycles shouldn't trigger a structural error
    visited.add(name)
    if name not in symtab or symtab[name].type != "composition":
        return None
    body = symtab[name].value
    last = body.operations[-1] if isinstance(body, SequenceNode) else body
    return _side_effect_verb(last, symtab, visited)


def _side_effect_verb(
    node: ASTNode,
    symtab: dict[str, SymbolEntry],
    visited: set[str],
) -> str | None:
    """Return the verb name if this AST node is side-effect-only at
    value position; None if it produces a value (v2b §76 + v2d §102
    extended table)."""
    if isinstance(node, ShowNode):
        return "show"
    if isinstance(node, FilterNode):
        return "filter"
    if isinstance(node, EachNode):
        return "each"
    if isinstance(node, ChooseNode):
        # v2d §102 — `choose` evaluates a condition and runs a branch
        # for its side effects; it does not produce a value.
        return "choose"
    if isinstance(node, FinishNode):
        # v3a §112 — `finish` is side-effect-only (and total-stop).
        # A composition whose last op is `finish` returns no value.
        return "finish"
    if isinstance(node, AddNode):
        # Liminate `add` v1 §5 — silent mutation; returns no value.
        return "add"
    if isinstance(node, RemoveNode):
        # `remove` — silent mutation; returns no value.
        return "remove"
    if isinstance(node, WeakensNode):
        # `weakens` — attaches decay metadata; returns no value.
        return "weakens"
    if isinstance(node, RequireNode):
        # Normative Era batch 2 — `require` either passes silently or
        # halts with REQUIREMENT_NOT_MET. Never produces a value.
        return "require"
    if isinstance(node, ExpectNode):
        # Epistemic Era batch 3 — `expect` is silent on pass; emits
        # divergence output on failure. Never produces a value.
        return "expect"
    if isinstance(node, AssignNode):
        # Delegated Era batch 3 — `assign` stores into the symbol
        # table; returns no value.
        return "assign"
    if isinstance(node, (RememberListNode, RememberRecordNode, RememberCompositionNode)):
        return "remember"
    if isinstance(node, RememberValueNode):
        # `remember ... from <verb-phrase>` is value-producing iff the
        # captured inner verb-phrase itself produces a value (§76 table).
        inner = node.value
        if isinstance(inner, (KeepNode, CombineNode, CountNode, GatherNode)):
            return None
        if isinstance(inner, CompositionCallNode):
            return _composition_void_result_verb(inner.name, symtab, visited)
        return "remember"
    if isinstance(node, CompositionCallNode):
        return _composition_void_result_verb(node.name, symtab, visited)
    # Bare value-producing verbs: keep, combine, count, gather.
    return None


def _check_arithmetic(
    node: ArithmeticNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
) -> None:
    """Infrastructure Era — validate both operands of a binary
    arithmetic expression. Both must be numeric (or resolvable to a
    number at runtime). QuotedString operands are rejected statically;
    NameRef operands must exist; FieldAccessNode operands must point at
    a numeric field; BareWord operands defer to runtime (they may
    resolve via the iterator context). Nested ArithmeticNode operands
    recurse.
    """
    _check_arithmetic_operand(node.left, symtab, iterator)
    _check_arithmetic_operand(node.right, symtab, iterator)


def _check_arithmetic_operand(
    operand: ASTNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
) -> None:
    if isinstance(operand, NumberLiteral):
        return
    if isinstance(operand, QuotedString):
        raise _SemanticError(
            f"Arithmetic only works with numbers, not text. "
            f"'{operand.content}' is text."
        )
    if isinstance(operand, ArithmeticNode):
        _check_arithmetic(operand, symtab, iterator)
        return
    if isinstance(operand, FieldAccessNode):
        _check_field_access(operand, symtab)
        entry = symtab[operand.record_name]
        ftype = (entry.schema or {}).get(operand.field)
        if ftype not in ("number", None, "unknown"):
            raise _SemanticError(
                f"Arithmetic only works with numbers, but "
                f"'{operand.field} of {operand.record_name}' is "
                f"{_singular(ftype)}."
            )
        return
    if isinstance(operand, NameRef):
        if operand.name not in symtab:
            raise _SemanticError(
                f"I can't find '{operand.name}'. "
                f"You might need to 'remember' it first."
            )
        t = symtab[operand.name].type
        if t not in ("number", "unknown"):
            raise _SemanticError(
                f"Arithmetic only works with numbers, but "
                f"'{operand.name}' is {_singular(t)}."
            )
        return
    if isinstance(operand, BareWord):
        # Defer to runtime — a BareWord may resolve via the iterator
        # context (e.g., `each ... add price multiplied by rate to ...`).
        # If it resolves to a non-numeric, the interpreter's runtime
        # numeric guard will produce the error.
        return
    if isinstance(operand, EachPronoun):
        # Inside an iterator over scalar numbers, `each` is numeric.
        return
    raise _SemanticError(
        f"Unexpected operand in arithmetic expression: {type(operand).__name__}."
    )


def _check_field_access(
    node: FieldAccessNode, symtab: dict[str, SymbolEntry],
) -> None:
    """v2b §77 — three semantic checks for `<field> of <record>` at any
    value position (same as v2a §68 in `show` target position):
    1. The record name resolves to a symbol.
    2. The symbol is a record (with U8 list-of-records guidance).
    3. The record's schema contains the field.
    """
    if node.record_name not in symtab:
        raise _SemanticError(
            f"I can't find '{node.record_name}'. "
            f"You might need to 'remember' it first."
        )
    entry = symtab[node.record_name]
    if entry.type != "record":
        if entry.type == "list_of_records":
            raise _SemanticError(
                f"'of' needs a single record. '{node.record_name}' "
                f"is a list of records — did you mean: "
                f"each the {node.record_name} show {node.field}?"
            )
        raise _SemanticError(
            f"'of' needs a record. '{node.record_name}' is "
            f"{_singular(entry.type)}."
        )
    if entry.schema is None or node.field not in entry.schema:
        raise _SemanticError(
            f"'{node.record_name}' doesn't have a field called '{node.field}'."
        )


def _check_remember_list(
    node: RememberListNode,
    symtab: dict[str, SymbolEntry],
    *,
    in_action_block: bool = False,
    live_value_names: set[str] | None = None,
) -> None:
    _check_live_value_remember(node.name, in_action_block, live_value_names)
    if not node.items:
        return  # empty list is valid — type will be inferred on first add
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
    if isinstance(item, QuotedString):
        # v2c §87: a quoted item in a list always contributes a string.
        return "string", item.content
    if isinstance(item, FieldAccessNode):
        # v2b §77: same semantic checks at list-item position.
        _check_field_access(item, symtab)
        entry = symtab[item.record_name]
        return entry.schema[item.field], f"{item.field} of {item.record_name}"
    if isinstance(item, ArithmeticNode):
        # Infrastructure Era — list items may be arithmetic expressions.
        _check_arithmetic(item, symtab, iterator=None)
        return "number", "arithmetic expression"
    raise _SemanticError(f"Unexpected list item {type(item).__name__}.")


def _check_remember_record(
    node: RememberRecordNode,
    symtab: dict[str, SymbolEntry],
    *,
    in_action_block: bool = False,
    live_value_names: set[str] | None = None,
) -> None:
    _check_live_value_remember(node.name, in_action_block, live_value_names)
    # Field values are single tokens (v1d §61), or v2b §77 field-access
    # expressions. NumberLiteral and BareWord field values are trivially
    # accepted (BareWords resolve at execution time per existing v1
    # semantics). FieldAccessNode values get the same three semantic
    # checks as any other v2b field access.
    if not node.fields:
        raise _SemanticError("A record needs at least one field.")
    for _fname, fexpr in node.fields:
        if isinstance(fexpr, FieldAccessNode):
            _check_field_access(fexpr, symtab)


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
    if isinstance(node.target, QuotedString):
        # v2c §88: literal display — no symbol resolution.
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


def _check_weakens(
    node: WeakensNode,
    symtab: dict[str, SymbolEntry],
    *,
    live_value_names: set[str] | None = None,
) -> None:
    """Metabolic Era batch 1 — validate the `weakens` verb.

    1. Subject must not be a live value (adapter-owned).
    2. Subject must exist in the symbol table.
    3. Subject must be numeric (or `unknown` — defer to runtime).
    4. Period must be a positive number.
    """
    name = node.subject.name
    names = live_value_names or set()
    if name in names:
        raise _SemanticError(
            f"'{name}' is a live value provided by the domain pack — "
            f"you can't apply decay to it directly."
        )
    if name not in symtab:
        raise _SemanticError(
            f"I can't find '{name}'. "
            f"You might need to 'remember' it first."
        )
    entry = symtab[name]
    if entry.type not in ("number", "unknown"):
        raise _SemanticError(
            f"'weakens' only works on numbers — "
            f"'{name}' is {_singular(entry.type)}."
        )
    if node.period.value <= 0:
        raise _SemanticError(
            f"The decay period must be a positive number, "
            f"not {_fmt_number(node.period.value)}."
        )


def _check_assign(
    node: AssignNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
    *,
    in_action_block: bool = False,
    live_value_names: set[str] | None = None,
) -> None:
    """Delegated Era batch 3 — validate the `assign` verb.

    1. Item must not be a live value (adapter-owned).
    2. Recipient value must be resolvable (NameRef must exist in
       symtab; BareWords, QuotedStrings, NumberLiterals are accepted
       unconditionally — BareWords fall back to string literals at
       runtime).
    """
    names = live_value_names or set()
    if node.item.name in names:
        raise _SemanticError(
            f"'{node.item.name}' is a live value provided by the domain "
            f"pack — you can't assign it directly."
        )
    _check_value_expr(
        node.recipient, symtab, iterator,
        in_action_block=in_action_block,
        live_value_names=live_value_names,
    )


def _check_filter(
    node: FilterNode,
    symtab: dict[str, SymbolEntry],
    *,
    live_value_names: set[str] | None = None,
) -> None:
    name = node.target.name
    # v3a §111/§117: `filter` is destructive. Adapter-owned live values
    # cannot be mutated by user code at any point — Phase 1 or Phase 2.
    if live_value_names and name in live_value_names:
        raise _SemanticError(
            f"'{name}' is a live value provided by the domain pack. "
            f"'filter' is destructive and can't modify it — use 'keep' "
            f"to read items without changing the source."
        )
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
    if cond.op in ("includes", "not_includes"):
        return  # list-membership — analyzer accepts any operand types
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
    if isinstance(value_node, QuotedString):
        # v2c §87: quoted value in a where comparison is always a string.
        return "string", value_node.content
    if isinstance(value_node, EachPronoun):
        if iterator.record_schemas is not None:
            return "record", "each"
        return iterator.scalar_type or "unknown", "each"
    if isinstance(value_node, FieldAccessNode):
        # v2b §77: <field> of <record> at the value position after an
        # operator. Same semantic checks; resolved type is the field's
        # scalar type from the record's schema.
        _check_field_access(value_node, symtab)
        entry = symtab[value_node.record_name]
        return (
            entry.schema[value_node.field],
            f"{value_node.field} of {value_node.record_name}",
        )
    if isinstance(value_node, ArithmeticNode):
        # Infrastructure Era — arithmetic on the right-hand side of a
        # condition. Result type is always number.
        _check_arithmetic(value_node, symtab, iterator)
        return "number", "arithmetic expression"
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


def _check_each(
    node: EachNode,
    symtab: dict[str, SymbolEntry],
    *,
    in_action_block: bool = False,
    live_value_names: set[str] | None = None,
) -> None:
    name = node.collection.name
    entry = _require_list(name, symtab, verb="iterate over")
    iterator = _make_iterator(name, entry)
    _check(
        node.action, symtab, iterator,
        in_action_block=in_action_block,
        live_value_names=live_value_names,
    )


# ---------------------------------------------------------------------------
# named-composition call (§23 line 466 / v1b §41)
# ---------------------------------------------------------------------------


def _check_composition_call(
    node: CompositionCallNode,
    symtab: dict[str, SymbolEntry],
    *,
    in_action_block: bool = False,
    live_value_names: set[str] | None = None,
) -> None:
    _check_composition_call_shape(node, symtab)
    _analyze_composition_body(
        node, symtab,
        in_action_block=in_action_block,
        live_value_names=live_value_names,
    )


def _check_composition_call_shape(
    node: CompositionCallNode,
    symtab: dict[str, SymbolEntry],
) -> None:
    """v2d §97 — verify the call shape matches the composition's
    signature: a parameter must be supplied iff the composition declared
    one. Existence/type checks come first so the user sees the most
    informative error.
    """
    if node.name not in symtab or symtab[node.name].type != "composition":
        raise _SemanticError(f"I can't find a composition called '{node.name}'.")
    entry = symtab[node.name]
    param = entry.composition_param

    if param is not None and node.arg is None:
        raise _SemanticError(
            f"'{node.name}' expects an input (from <{param}>). "
            f"Try: {node.name} from <your-list>."
        )
    if param is None and node.arg is not None:
        raise _SemanticError(
            f"'{node.name}' doesn't take an input. "
            f"Call it on its own: {node.name}."
        )
    if node.arg is not None and node.arg not in symtab:
        raise _SemanticError(
            f"I can't find '{node.arg}'. "
            f"You might need to 'remember' it first."
        )


def _analyze_composition_body(
    node: CompositionCallNode,
    symtab: dict[str, SymbolEntry],
    *,
    in_action_block: bool = False,
    live_value_names: set[str] | None = None,
) -> None:
    """Analyze the composition body with the parameter temporarily bound
    to the passed argument's entry (v2d §96). Restore the prior binding
    (if any) on exit so the analyzer leaves the symbol table as it found
    it. Mirrors the runtime save/bind/exec/restore shape (interpreter),
    so a body that references `data` resolves the same way at analyze
    time as it will at execution time.

    v3a: `in_action_block` propagates into the body so FinishNode and
    live-value ownership rules apply consistently — a `finish` inside
    a composition called from an action block is legal, but the same
    composition called at top level (Phase 1) fails (§112).
    """
    entry = symtab[node.name]
    body = entry.value
    param = entry.composition_param
    if param is None or node.arg is None:
        _check(
            body, symtab, iterator=None,
            in_action_block=in_action_block,
            live_value_names=live_value_names,
        )
        return
    original = symtab.get(param)
    symtab[param] = symtab[node.arg]  # alias for analysis only
    try:
        _check(
            body, symtab, iterator=None,
            in_action_block=in_action_block,
            live_value_names=live_value_names,
        )
    finally:
        if original is None:
            symtab.pop(param, None)
        else:
            symtab[param] = original


# ---------------------------------------------------------------------------
# choose (v2d §99–§102)
# ---------------------------------------------------------------------------


def _check_choose(
    node: ChooseNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
    *,
    in_action_block: bool = False,
    live_value_names: set[str] | None = None,
) -> None:
    """Validate each branch's condition + action. Conditions use the
    choose-specific operand resolver (no iterator context per §100);
    actions are analyzed against whatever iterator the surrounding scope
    provides (None at top level — choose-inside-each is rejected at
    parse time per §102)."""
    for br in node.branches:
        if br.condition is not None:
            _check_choose_condition(br.condition, symtab)
        _check(
            br.action, symtab, iterator,
            in_action_block=in_action_block,
            live_value_names=live_value_names,
        )


def _check_choose_condition(
    cond: ASTNode,
    symtab: dict[str, SymbolEntry],
) -> None:
    if isinstance(cond, CompoundConditionNode):
        _check_choose_condition(cond.left, symtab)
        _check_choose_condition(cond.right, symtab)
        return
    if not isinstance(cond, ConditionNode):
        raise _SemanticError("Unexpected condition shape.")
    field_type, field_label = _resolve_choose_operand(cond.field, symtab)
    value_type, value_label = _resolve_choose_operand(cond.value, symtab)
    if cond.op in ("is", "equal_to"):
        return
    if cond.op in ("above", "below"):
        _require_numeric(field_type, field_label, cond.op)
        _require_numeric(value_type, value_label, cond.op)
        return
    if cond.op in ("includes", "not_includes"):
        return
    if cond.op.startswith("not_"):
        inner = cond.op[len("not_"):]
        if inner in ("above", "below"):
            _require_numeric(field_type, field_label, f"not {inner}")
            _require_numeric(value_type, value_label, f"not {inner}")
        return
    raise _SemanticError(f"Unknown comparison operator '{cond.op}'.")


# ---------------------------------------------------------------------------
# when / finish (v3a §108, §109, §112)
# ---------------------------------------------------------------------------


def _check_when(
    node: WhenNode,
    symtab: dict[str, SymbolEntry],
) -> None:
    """v3a §108/§109: registration-time validation for a `when` handler.

    Only the condition and (optional) unless guard are validated here —
    all names referenced in either must exist in the symbol table at the
    point the `when` statement is encountered (§108 "Registration-time
    name resolution"). The action block itself is not analyzed at
    registration; per §108/§111 name resolution inside actions is
    deferred to firing time because actions may reference values created
    by other handlers or by adapter updates.
    """
    _check_choose_condition(node.condition, symtab)
    if node.unless is not None:
        _check_choose_condition(node.unless, symtab)


def _check_pack_verb(
    node: PackVerbNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None = None,
    *,
    live_value_names: set[str] | None = None,
) -> None:
    """v4a §137 + v2 (pack verb contract extension) — validate slot
    type_constraints, then dispatch on execution type for additional
    checks.

    Slots whose `value_type == "value"` may carry NumberLiteral,
    QuotedString, BareWord, or FieldAccessNode — only NameRef slots are
    checked for type_constraint matching, and only NameRef-resolvable
    slots can carry a constraint at all (the type table refers to symbols).
    """
    for slot in node.signature.slots:
        if slot.name not in node.slot_values:
            continue
        value_node = node.slot_values[slot.name]
        if slot.type_constraint is None:
            # No type constraint — anything goes at this layer; execution
            # checks below may still resolve names.
            continue
        if not isinstance(value_node, NameRef):
            slot_label = _pack_slot_label(node.word, slot)
            raise _SemanticError(
                f"'{slot_label}' expects a name."
            )
        name = value_node.name
        if name not in symtab:
            raise _SemanticError(
                f"I can't find '{name}'. "
                f"You might need to 'remember' it first."
            )
        entry = symtab[name]
        constraint = slot.type_constraint
        slot_label = _pack_slot_label(node.word, slot)
        descriptor = (entry.descriptor or "").lower()
        if descriptor != constraint.lower():
            # SC-Q1 prerequisite: type_constraint applies regardless of
            # the variable's underlying Liminate type. A string with the
            # right descriptor passes; a string with no descriptor fails
            # with a message that names the type.
            if entry.descriptor:
                shown = f"a {entry.descriptor}"
            elif entry.type == "record":
                shown = "a record"
            else:
                shown = _singular(entry.type)
            raise _SemanticError(
                f"'{name}' is {shown}, not a {constraint}. "
                f"'{slot_label}' expects a {constraint}."
            )

    # v2 — execution-type-specific validation.
    execution = node.signature.execution
    if isinstance(execution, SubstringCheckExecution):
        _check_pack_substring(node, execution, symtab)
    elif isinstance(execution, AppendToListExecution):
        _check_pack_append(
            node, execution, symtab, iterator,
            live_value_names=live_value_names,
        )
    elif isinstance(execution, SetFieldExecution):
        _check_pack_set_field(node, execution, symtab)
    elif isinstance(execution, CompareValuesExecution):
        _check_pack_compare(node, execution, symtab)
    elif isinstance(execution, NumericExtractCompareExecution):
        _check_pack_numeric_extract(node, execution, symtab)
    # SetValueExecution: nothing further beyond type_constraint loop.


def _pack_slot_label(verb: str, slot) -> str:
    """v2 — friendly label for a pack slot in error messages. Positional
    slots use `<verb> <slot-name>`; connective-introduced use
    `<verb> <connective>`."""
    if slot.connective is None:
        return f"{verb} {slot.name}"
    return f"{verb} {slot.connective}"


def _resolve_slot_target_name(
    node: PackVerbNode, execution, symtab,
) -> str:
    """v2 — resolve a write-target execution's target to a symbol name.
    Used by analyzer checks. Mirrors the interpreter's `_resolve_target`."""
    if execution.target_slot is not None:
        value_node = node.slot_values.get(execution.target_slot)
        if isinstance(value_node, NameRef):
            return value_node.name
        if isinstance(value_node, BareWord):
            return value_node.word
        raise _SemanticError(
            f"Pack verb '{node.word}' needs a name for its target."
        )
    return execution.target_name


def _check_pack_substring(
    node: PackVerbNode,
    execution: SubstringCheckExecution,
    symtab: dict[str, SymbolEntry],
) -> None:
    """v2 §4 — `substring_check` analyzer validation."""
    against_node = node.slot_values.get(execution.against_slot)
    if not isinstance(against_node, NameRef):
        raise _SemanticError(
            f"'{node.word}' expects a name for the source text."
        )
    name = against_node.name
    if name not in symtab:
        raise _SemanticError(
            f"I can't find '{name}'. "
            f"You might need to 'remember' it first."
        )
    entry = symtab[name]
    if entry.type != "string":
        raise _SemanticError(
            f"'{node.word} from' expects text, but '{name}' is "
            f"{_singular(entry.type)}."
        )
    # check_slot: NameRef must exist; literals/field-access trivially valid.
    check_node = node.slot_values.get(execution.check_slot)
    if isinstance(check_node, NameRef):
        if check_node.name not in symtab:
            raise _SemanticError(
                f"I can't find '{check_node.name}'. "
                f"You might need to 'remember' it first."
            )
    elif isinstance(check_node, FieldAccessNode):
        _check_field_access(check_node, symtab)


def _check_pack_append(
    node: PackVerbNode,
    execution: AppendToListExecution,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
    *,
    live_value_names: set[str] | None,
) -> None:
    """v2 §5 — `append_to_list` analyzer validation."""
    target_name = _resolve_slot_target_name(node, execution, symtab)
    if execution.source_slot is not None:
        item_node = node.slot_values.get(execution.source_slot)
        if item_node is None:
            raise _SemanticError(
                f"Pack verb '{node.word}' missing source value."
            )
    else:
        # literal_value — synthesize a QuotedString item for type inference.
        item_node = QuotedString(content=execution.literal_value or "")
    _check_list_append(
        target_name, item_node, symtab, iterator,
        live_value_names=live_value_names,
        verb=node.word,
    )


def _check_pack_set_field(
    node: PackVerbNode,
    execution: SetFieldExecution,
    symtab: dict[str, SymbolEntry],
) -> None:
    """v2 §6 — `set_field` analyzer validation."""
    target_name = _resolve_slot_target_name(node, execution, symtab)
    if target_name not in symtab:
        raise _SemanticError(
            f"I can't find '{target_name}'. "
            f"You might need to 'remember' it first."
        )
    entry = symtab[target_name]
    if entry.type != "record":
        raise _SemanticError(
            f"'{node.word}' expects a record, but '{target_name}' is "
            f"{_singular(entry.type)}."
        )
    if execution.source_slot is not None:
        src = node.slot_values.get(execution.source_slot)
        if isinstance(src, NameRef) and src.name not in symtab:
            raise _SemanticError(
                f"I can't find '{src.name}'. "
                f"You might need to 'remember' it first."
            )
        elif isinstance(src, FieldAccessNode):
            _check_field_access(src, symtab)


def _check_pack_compare(
    node: PackVerbNode,
    execution: CompareValuesExecution,
    symtab: dict[str, SymbolEntry],
) -> None:
    """v2 §7 — `compare_values` analyzer validation."""
    for slot_name in (execution.left_slot, execution.right_slot):
        value_node = node.slot_values.get(slot_name)
        if not isinstance(value_node, NameRef):
            raise _SemanticError(
                f"'{node.word}' expects a name for '{slot_name}'."
            )
        if value_node.name not in symtab:
            raise _SemanticError(
                f"I can't find '{value_node.name}'. "
                f"You might need to 'remember' it first."
            )


def _check_pack_numeric_extract(
    node: PackVerbNode,
    execution: NumericExtractCompareExecution,
    symtab: dict[str, SymbolEntry],
) -> None:
    """Analyzer validation for numeric_extract_compare."""
    against_node = node.slot_values.get(execution.against_slot)
    if not isinstance(against_node, NameRef):
        raise _SemanticError(
            f"'{node.word}' expects a name for the source text."
        )
    name = against_node.name
    if name not in symtab:
        raise _SemanticError(
            f"I can't find '{name}'. "
            f"You might need to 'remember' it first."
        )
    entry = symtab[name]
    if entry.type != "string":
        raise _SemanticError(
            f"'{node.word} from' expects text, but '{name}' is "
            f"{_singular(entry.type)}."
        )


def _check_finish(
    node: FinishNode,
    *,
    in_action_block: bool,
) -> None:
    """v3a §112: `finish` is the listener-mode exit verb. It is legal
    only inside a `when` action block — directly, in a `choose` branch,
    or in a composition called from one. Phase 1 sequential calls (or
    composition-bodied `finish` reached during sequential mode) are
    semantic errors at the call site."""
    if not in_action_block:
        raise _SemanticError(
            "'finish' can only be used inside an event handler."
        )


# ---------------------------------------------------------------------------
# add (Liminate `add` v1 §10)
# ---------------------------------------------------------------------------


_LIST_ITEM_CATEGORY = {
    "list_of_numbers": "number",
    "list_of_strings": "string",
    "list_of_records": "record",
}


def _check_add(
    node: AddNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
    *,
    live_value_names: set[str] | None = None,
) -> None:
    """v1 §10 — `add` verb validation, factored to `_check_list_append`."""
    _check_list_append(
        node.target.name, node.item, symtab, iterator,
        live_value_names=live_value_names,
        verb="add",
    )


def _check_remove(
    node: RemoveNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
    *,
    live_value_names: set[str] | None = None,
) -> None:
    """`remove` verb validation — same shape as `_check_add`.

    Reuses `_check_list_append`: live-value restriction, target exists
    and is a list, item resolves to a value, self-mutation guard inside
    `each`. The element-category match is also enforced — removing a
    number from a list of strings is a static error regardless of
    runtime contents.
    """
    _check_list_append(
        node.target.name, node.item, symtab, iterator,
        live_value_names=live_value_names,
        verb="remove",
    )


def _check_list_append(
    target_name: str,
    item_node: ASTNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
    *,
    live_value_names: set[str] | None,
    verb: str,
) -> None:
    """v2 — shared list-append/retract validation. Five checks:
      1. Live-value restriction (§7).
      2. Target exists and is a list.
      3. Item resolves to a value (NameRef must exist; field access checked).
      4. Item type matches the list's element category (§3).
      5. Self-mutation guard inside `each` (§6).
    """
    # `add` reads naturally with "to"; `remove` reads with "from".
    prep = "from" if verb == "remove" else "to"
    names = live_value_names or set()
    if target_name in names:
        raise _SemanticError(
            f"'{target_name}' is a live value provided by the domain pack. "
            f"'{verb}' modifies the list and can't be used on it — the "
            f"domain pack controls this value."
        )
    if target_name not in symtab:
        raise _SemanticError(
            f"I can't find '{target_name}'. "
            f"You might need to 'remember' it first."
        )
    entry = symtab[target_name]
    if entry.type not in _LIST_ITEM_CATEGORY:
        raise _SemanticError(
            f"I can only {verb} {prep} a list. "
            f"'{target_name}' is {_singular(entry.type)}."
        )

    if iterator is not None and iterator.collection_name == target_name:
        raise _SemanticError(
            f"'{target_name}' is the list being iterated — you can't "
            f"{verb} {prep} it while iterating. "
            f"Try {verb}ing {prep} a different list."
        )

    item_type, item_label = _infer_add_item_type(item_node, symtab, iterator)
    expected = _LIST_ITEM_CATEGORY[entry.type]
    if (
        not entry.value
        or (
            entry.type == "list_of_strings"
            and all(v == "none" for v in entry.value)
        )
    ):
        return
    if item_type != expected:
        action = "removed from" if verb == "remove" else "added to"
        raise _SemanticError(
            f"'{target_name}' is {_singular(entry.type)}. "
            f"'{item_label}' is {_singular(item_type)} and can't be {action} it."
        )


def _infer_add_item_type(
    item: ASTNode,
    symtab: dict[str, SymbolEntry],
    iterator: IteratorContext | None,
) -> tuple[str, str]:
    """Resolve an `add` item to (type, label). Iterator-first per v1c §49:
    inside `each <list-of-records>`, a BareWord matching a field on every
    iterated record resolves to that field's type."""
    if isinstance(item, NumberLiteral):
        return "number", _fmt_number(item.value)
    if isinstance(item, QuotedString):
        return "string", item.content
    if isinstance(item, FieldAccessNode):
        _check_field_access(item, symtab)
        entry = symtab[item.record_name]
        return entry.schema[item.field], f"{item.field} of {item.record_name}"
    if isinstance(item, BareWord):
        word = item.word
        if (
            iterator is not None
            and iterator.record_schemas is not None
            and all(word in s for s in iterator.record_schemas)
        ):
            types = {s[word] for s in iterator.record_schemas}
            return (next(iter(types)) if len(types) == 1 else "mixed"), word
        if word in symtab:
            return symtab[word].type, word
        return "string", word
    if isinstance(item, NameRef):
        if item.name not in symtab:
            raise _SemanticError(
                f"I can't find '{item.name}'. "
                f"You might need to 'remember' it first."
            )
        return symtab[item.name].type, item.name
    if isinstance(item, ArithmeticNode):
        # Infrastructure Era — `add <expr> to <list>` accepts arithmetic
        # expressions; the result is always numeric.
        _check_arithmetic(item, symtab, iterator)
        return "number", "arithmetic expression"
    raise _SemanticError(f"Unexpected item for 'add': {type(item).__name__}.")


def _resolve_choose_operand(
    node: ASTNode,
    symtab: dict[str, SymbolEntry],
) -> tuple[str, str]:
    """Resolve a condition operand inside `choose if`. No iterator
    context — names resolve directly against the symbol table; field
    access uses `<field> of <record>` explicitly (§100)."""
    if isinstance(node, NumberLiteral):
        return "number", _fmt_number(node.value)
    if isinstance(node, BareWord):
        if node.word in symtab:
            return symtab[node.word].type, node.word
        return "string", node.word
    if isinstance(node, QuotedString):
        return "string", node.content
    if isinstance(node, NameRef):
        if node.name not in symtab:
            raise _SemanticError(
                f"I can't find '{node.name}'. "
                f"You might need to 'remember' it first."
            )
        return symtab[node.name].type, node.name
    if isinstance(node, FieldAccessNode):
        _check_field_access(node, symtab)
        entry = symtab[node.record_name]
        return (
            entry.schema[node.field],
            f"{node.field} of {node.record_name}",
        )
    if isinstance(node, EachPronoun):
        raise _SemanticError(
            "'each' only refers to the current item inside an 'each' or "
            "'where' clause. In 'choose', name the value directly."
        )
    if isinstance(node, ArithmeticNode):
        # Infrastructure Era — arithmetic operands inside `choose` /
        # `require` / `expect` conditions resolve to numbers.
        _check_arithmetic(node, symtab, iterator=None)
        return "number", "arithmetic expression"
    raise _SemanticError("Unexpected operand in 'choose' condition.")


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

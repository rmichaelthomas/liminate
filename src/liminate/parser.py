"""Parser for Liminate v1.

Sources:
- inception §17 (slot-filling, verb signatures)
- inception §21 (and/or context rules, is dual role, not modifier, compound conditions)
- inception §22 (lexer feeds the parser; unknown-word positional classification)
- v1a §29 (reserved-word enforcement at name positions)
- v1a §30 (mixed and/or in `where` → AMBER_PRECEDENCE)
- v1a §33 (canonical prose rendering is a parser output requirement — done in renderer.py)
- v1b §36 (descriptors between article and `called` are decorative)
- v1b §37 (`each` dual role — pronoun inside `where`)
- v1b §41 (named-composition call falls back to symbol table when no verb)
- v1b §43 (`from` disambiguation in `remember`)
- v1b §44 (complete disambiguation ruleset)
- v1c §46 (vocabulary words cannot be string values)
- v1c §51 (parser lookahead + clause-context tracking)
- v1d §58 (duplicate `remember` names overwrite — interpreter concern)
- v1d §60/§61 (record schemas, single-token strings)
- Meta-Structural Era (`about` declaration): `AboutNode` + `parse_about`,
  a separate top-level entry point called by the CLI for the first
  non-blank, non-comment line. `about` is rejected inside the normal
  `parse()` pipeline (declarations are first-line-only, MS-Q1).

Output:
- An AST node on success.
- An LiminateResult on amber (mixed-precedence) or parse error.

Note on the "list" descriptor (v1b §36 + v1d §65 sentence 38):
v1b §36 states unknown words between article and `called` are decorative.
However v1d §65 sentence 38 (`remember a list called orders with order1`)
requires that single-item construct to produce a list of one item, not a
flat value — otherwise the downstream `filter the orders where missingfield
is above 50` would error as "I can only filter a list" rather than as the
spec-mandated "doesn't have a field called 'missingfield'". The parser
therefore captures the word `list` when it appears as a descriptor and
uses it to force list construction for singleton `with X` clauses. All
other descriptors remain decorative.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .result import LiminateResult, ResultStatus
from .vocabulary import (
    TOMBSTONES,
    PackVerbSignature,
    Token,
    TokenType,
    get_active_pack_verb,
    reserved_category,
)

# ---------------------------------------------------------------------------
# AST nodes
# ---------------------------------------------------------------------------


@dataclass
class ASTNode:
    pass


@dataclass
class NumberLiteral(ASTNode):
    value: int | float


@dataclass
class BareWord(ASTNode):
    """An unknown word in a value position (after `with`, after `as`, list
    items). The analyzer resolves it: if the name exists in the symbol
    table, copy that value; otherwise treat it as a string literal."""
    word: str


@dataclass
class NameRef(ASTNode):
    """An unknown word used as a reference (target, field, source).
    At runtime, resolves first against the iterator context (a field on
    the current item) and then against the symbol table (v1c §49)."""
    name: str


@dataclass
class EachPronoun(ASTNode):
    """The `each` pronoun inside a `where` clause (v1b §37). Resolves to
    the current scalar item being tested."""
    pass


@dataclass
class RememberValueNode(ASTNode):
    name: str
    value: ASTNode
    # The user's descriptor between article and `called` (v2a §71 / D6).
    # Preserved verbatim in canonical rendering. None when the user wrote
    # nothing between article and `called` (or omitted the article); the
    # renderer falls back to the inferred type label ("value").
    # Excluded from __eq__ because descriptors are semantically decorative
    # (v1b §36) — two ASTs that differ only in descriptor are equivalent.
    descriptor: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 2 — optional `because "<rationale>"` clause.
    # Inert metadata: rendered and inspected, never executed. Excluded from
    # __eq__ on the same grounds as `descriptor` — two ASTs differing only
    # in rationale are semantically equivalent at execution time.
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class RememberListNode(ASTNode):
    name: str
    items: list[ASTNode]
    # v2a §71 / D6 — see RememberValueNode for rationale.
    descriptor: str | None = field(default=None, compare=False)
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class RememberRecordNode(ASTNode):
    name: str
    fields: list[tuple[str, ASTNode]]
    # v2a §71 / D6 — see RememberValueNode for rationale.
    descriptor: str | None = field(default=None, compare=False)
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class RememberCompositionNode(ASTNode):
    name: str
    body: ASTNode
    # v2d §96 — optional single named parameter. None when the composition
    # was defined without a `from <param>` clause (the v1/v2a/v2b/v2c shape).
    # The parameter name follows v1's name rules (UNKNOWN token, reserved-
    # word exclusion via _consume_name).
    param: str | None = None
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class QuotedString(ASTNode):
    """v2c §86/§87/§88 — a quoted-string literal. Always evaluates to its
    content as a string in value positions (no symbol-table fallback,
    unlike BareWord). When it appears as a `show` target, the interpreter
    displays the literal text (§88)."""
    content: str


@dataclass
class FieldAccessNode(ASTNode):
    """v2b §77 — `<field> of <record>` as a value expression at any value
    position (after `with`, after `as`, after operators in `where`).
    Single-level only; chained `of` (a of b of c) is a parse error.
    Existing v2a §68 `show <field> of <record>` is still represented on
    ShowNode (a special case of the general rule)."""
    field: str
    record_name: str


@dataclass
class ShowNode(ASTNode):
    target: ASTNode | None  # None = display the current iterator item
    # v2a §68 (D4) — `of` field access: when present, `target` is the
    # field name (NameRef) and `record_name` is the record symbol to
    # look it up on. e.g. `show total of order1` → target=NameRef("total"),
    # record_name="order1".
    record_name: str | None = None
    # v2a §69 (D1) — multi-field display inside `each ... show`.
    # When non-empty, lists *additional* field names after the first
    # (which lives in `target`). Per-record output is rendered as
    # `field1: value1, field2: value2, ...`. Only valid when this
    # ShowNode is the body of an EachNode and `target` is a NameRef.
    extra_fields: list[str] = field(default_factory=list)
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class FilterNode(ASTNode):
    target: NameRef
    condition: ASTNode
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class KeepNode(ASTNode):
    """v2a §67 — non-destructive sibling of FilterNode. Same shape: a
    target list and a condition. Difference is purely semantic: keep
    returns a new list without modifying the source's symbol-table
    entry. Compositions wrapping `keep` are reusable on the same data
    (resolving D3)."""
    target: NameRef
    condition: ASTNode
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class CountNode(ASTNode):
    target: NameRef
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class GatherNode(ASTNode):
    name: str
    from_val: int | float
    to_val: int | float
    # D-6 — optional step value. None means the default step (1). The step
    # is always stored positive; the direction (ascending vs descending) is
    # derived from comparing from_val and to_val, never from the step sign.
    step_val: int | float | None = None
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class SumNode(ASTNode):
    target: NameRef
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class EachNode(ASTNode):
    collection: NameRef
    action: ASTNode
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class CompositionCallNode(ASTNode):
    name: str
    # v2d §96 / Phase 2 D-1 — optional parameter-passing argument. None when
    # the call provided no `from <arg>` clause. A `str` is a bare-name
    # reference resolved against the symbol table at run time (the v2d §96
    # path). An `ASTNode` is a self-contained literal atom — `NumberLiteral`
    # or `QuotedString` (D-1). Every reader (parser, analyzer, interpreter,
    # renderer) must branch on `isinstance(arg, str)` before a symtab lookup.
    arg: "str | ASTNode | None" = None
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class SequenceNode(ASTNode):
    """A sequence of operations joined by `and` or `then`.

    Normative Era batch 2 added `then` as a sequencing connective with
    declared ordering intent. `connectors[i]` is the join word ("and"
    or "then") between `operations[i]` and `operations[i+1]`, so the
    list has length `len(operations) - 1`. An empty `connectors` list
    falls back to "and" for backward compatibility with callers that
    construct sequences without specifying joins.
    """
    operations: list[ASTNode]
    connectors: list[str] = field(default_factory=list)


@dataclass
class ConditionNode(ASTNode):
    field: ASTNode               # NameRef or EachPronoun
    op: str                      # is, above, below, equal_to, not_above, not_below, not_equal_to, within, includes
    value: ASTNode               # NumberLiteral, BareWord, NameRef, EachPronoun
    # Second right-hand operand, used only by the `within` numeric-tolerance
    # operator (issue #19): `<field> is within <value> of <value2>` is true
    # when |field - value2| <= value. None for every other operator.
    value2: ASTNode | None = None


@dataclass
class CompoundConditionNode(ASTNode):
    left: ASTNode
    right: ASTNode
    connector: str               # "and" or "or"


@dataclass
class ChooseBranch:
    """v2d §99–§101 — one (condition, action) pair inside a `choose`.

    A terminal `otherwise <action>` branch has `condition=None`. Branches
    are evaluated in order; the first whose condition is true fires (or,
    for the terminal branch, fires unconditionally as a fallback).
    """
    condition: ASTNode | None
    action: ASTNode


@dataclass
class ChooseNode(ASTNode):
    """v2d §99 — conditional branching verb.

    `branches` lists each branch in source order. The last branch may
    have `condition=None` (terminal `otherwise`). A bare `choose if X: A`
    is represented as a single-branch list with no terminal.
    """
    branches: list[ChooseBranch]
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class WhenNode(ASTNode):
    """v3a §108/§109 — top-level reactive handler.

    `condition` is the when-AST (choose-style operand resolution — symbol
    table names, `of` expressions; no iterator context). `unless` is the
    optional guard AST (§109): when present, the compound eligibility is
    `condition AND NOT unless`. `action` is the action block contents —
    a single AST for single-statement blocks, or a SequenceNode for the
    multi-line indented form (§110/§111).

    `when` is registered during Phase 1 (§108) but its action block does
    not execute until Phase 2 (§107). Name resolution inside `action` is
    deferred to firing time (§111); names in `condition`/`unless` are
    resolved at registration time.
    """
    condition: ASTNode
    unless: ASTNode | None
    action: ASTNode
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution, extended to `when` blocks. Inert provenance metadata
    # (compare=False). When a `when` handler is marked `inherited`, its
    # HANDLER_FIRE results carry the flag in their trigger metadata so
    # downstream consumers (Invariant) can distinguish pre-flight
    # checklist handlers from session-authored handlers.
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)


@dataclass
class PackVerbNode(ASTNode):
    """v4a §137 — a call to a pack-defined verb.

    `word` is the verb name as written. `signature` carries the verb's
    slot signature and execution definition (from the pack JSON), so the
    analyzer and interpreter can validate and dispatch without consulting
    the pack registry a second time. `slot_values` maps each filled
    slot's `name` to the AST value parsed for that slot (typically a
    NameRef per v4a; the dataclass is permissive so future packs can
    accept literals).
    """
    word: str
    signature: PackVerbSignature
    slot_values: dict[str, ASTNode] = field(default_factory=dict)
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class AddNode(ASTNode):
    """Liminate `add` v1 §10 — append an item to an existing list.

    `item` is the value being appended (NumberLiteral, BareWord, NameRef,
    QuotedString, or FieldAccessNode — same value types accepted by
    `remember ... with`). `target` is the list receiving the item.
    """
    item: ASTNode
    target: NameRef
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class RemoveNode(ASTNode):
    """Retract an item from an existing list.

    Same slot shape as `AddNode`: `item` is the value being removed and
    `target` is the list to remove from. Runtime error if `item` is not
    in the list — `remove` is explicit, not silent.
    """
    item: ASTNode
    target: NameRef
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class WeakensNode(ASTNode):
    """Metabolic Era batch 1 — autonomous linear decay verb.

    `subject` is a NameRef to an existing numeric variable. `period` is
    a NumberLiteral — the decay period in abstract ticks.
    """
    subject: NameRef
    period: NumberLiteral
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class FinishNode(ASTNode):
    """v3a §112 — exit listener mode immediately and totally.

    No slots. Legal only inside a `when` action block (directly, inside
    a `choose` branch, or inside a composition called from an action
    block). `finish` during Phase 1 is a semantic error.
    """
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class RequireNode(ASTNode):
    """Normative Era batch 2 — enforcement verb.

    Evaluates `condition`; if true, execution continues silently. If
    false, execution halts with REQUIREMENT_NOT_MET. The condition uses
    the same AST shapes as `choose if` / `where` conditions: ConditionNode
    leaves and CompoundConditionNode `and`/`or` combinators.

    v28 — `exception` is an optional `unless <condition>` clause. Unlike
    `rationale` (inert metadata), the exception changes the verb's truth
    table, so it participates in equality comparison (default compare=True).
    """
    condition: ASTNode
    exception: ASTNode | None = None
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class RequireEachNode(ASTNode):
    """v8a §49 — iterated enforcement verb.

    Evaluates `condition` once per element in `collection`, with
    `binding_name` bound to the current element as a temporary
    symbol-table entry. If any element violates the condition,
    execution halts with REQUIREMENT_NOT_MET. If all pass, silent.

    The condition uses the same unified condition grammar as
    RequireNode / ForbidNode / FilterNode / ChooseNode — inherited
    wholesale from `_parse_or_condition`. A condition that elides its
    field (begins with `is`/`includes`) binds to the current element
    via an implicit `EachPronoun`; an explicit reference to
    `binding_name` resolves to the same element (a NameRef).
    """
    binding_name: str
    collection: NameRef
    condition: ASTNode
    rationale: str | None = field(default=None, compare=False)
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class ForbidNode(ASTNode):
    """Deontic Era — prohibition verb.

    Evaluates `condition`; if true, execution halts with
    PROHIBITION_VIOLATED. If false, silent pass. Same condition AST
    as `require` / `choose if` / `where`. Mirrors `require` with
    inverted polarity.

    v28 — `exception` is an optional `unless <condition>` clause (see
    RequireNode for the compare=True rationale).
    """
    condition: ASTNode
    exception: ASTNode | None = None
    rationale: str | None = field(default=None, compare=False)
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class PermitNode(ASTNode):
    """Deontic Era — explicit permission verb.

    Evaluates `condition`; if true, emits an output line recording
    the permission. If false, silent pass. Never halts. Same
    condition AST as `require` / `forbid` / `choose if` / `where`.
    Completes the deontic triangle: require (obligation), forbid
    (prohibition), permit (permission).

    v28 — `exception` is an optional `unless <condition>` clause that
    narrows the permission (see RequireNode for the compare=True
    rationale).
    """
    condition: ASTNode
    exception: ASTNode | None = None
    rationale: str | None = field(default=None, compare=False)
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class AssignNode(ASTNode):
    """Delegated Era batch 3 — assignment/delegation verb.

    `item` is a NameRef — the variable name for the assignment
    (parsed via `_consume_target`). `recipient` is any value AST
    node — the actor or entity receiving the assignment (parsed
    via `_parse_value`).

    Runtime: `_store(symtab, item.name, evaluated_recipient)`.
    """
    item: NameRef
    recipient: ASTNode
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class ArithmeticNode(ASTNode):
    """Infrastructure Era — binary arithmetic expression.

    Represents `<left> <op> <right>` where op is one of: plus, minus,
    multiplied_by, divided_by. PEMDAS precedence is encoded by the
    shape of the tree (multiplicative nodes nest inside additive ones);
    same-tier operators are left-associative.
    """
    left: ASTNode
    right: ASTNode
    op: str  # "plus", "minus", "multiplied_by", "divided_by"


@dataclass
class ExtremaNode(ASTNode):
    """v25 — `highest`/`lowest` list-extrema selector (value expression).

    Form A (flat lists):   highest of <list>          -> field is None
    Form B (record lists): highest <field> of <list>  -> field is set
    Value-returning in both modes (VW-Q3): the scalar extremum. No
    statement metadata fields (rationale/inherited/starting/until) —
    this is a value node like ArithmeticNode/FieldAccessNode, never a
    statement in its own right.
    """
    word: str          # "highest" | "lowest"
    target: NameRef    # the list
    field: str | None = None


@dataclass
class SortNode(ASTNode):
    """Infrastructure Era batch 2 — sort a list in place by a field.

    `target` is the list to sort. `field` is the field name to sort by.
    `descending` is True when the `reverse` modifier is present
    (optionally preceded by the word `in`).
    """
    target: NameRef
    field: str
    descending: bool = False
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class CompareNode(ASTNode):
    """V2 promotion — structured comparison of two domain values.

    `left` and `right` are NameRefs to values in the symbol table. The
    interpreter infers comparison mode from operand types and stores a
    record named `comparison` with fields `status` (string) and
    `divergences` (list) in the symbol table.
    """
    left: NameRef
    right: NameRef
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class TransformNode(ASTNode):
    """Final V2 promotion — per-element list mutation.

    Two modes, distinguished by whether `field` is set:
    - Record-field mode (`field` is not None): modifies the named field
      on each record in `target`. Grammar: `transform <field> of
      <target> by <expression>`.
    - Scalar-list mode (`field` is None): replaces each scalar element
      in `target` with the expression result. Grammar: `transform
      <target> by <expression>`.

    `expression` is evaluated per element with iterator context — names
    resolve against the current element first, then the symbol table
    (v1c §49).
    """
    target: NameRef
    expression: ASTNode
    # `rationale` is declared before `field` because assigning the `field`
    # attribute below rebinds the name `field` in this class body, which
    # would shadow the imported `dataclasses.field` for any later call.
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)
    field: str | None = None


@dataclass
class ExpectNode(ASTNode):
    """Epistemic Era batch 3 — tracked anticipation verb.

    Evaluates `condition`; if true, silent pass. If false, emits
    an output line reporting the divergence. Program continues
    with SUCCESS — expectations are informational, not blocking.
    Same condition AST as `require` / `choose if` / `where`.

    v28 — `exception` is an optional `unless <condition>` clause (see
    RequireNode for the compare=True rationale).
    """
    condition: ASTNode
    exception: ASTNode | None = None
    rationale: str | None = field(default=None, compare=False)
    # Meta-Structural Era batch 3 — `inherited` operator + `from`
    # attribution. Both are inert provenance metadata (compare=False),
    # never read by execution. `inherited` marks the statement as carried
    # forward from a prior context; `inherited_from` names the authoring
    # agent (MS-Q3 overridable / MS-Q4 reuse `from`).
    inherited: bool = field(default=False, compare=False)
    inherited_from: str | None = field(default=None, compare=False)
    # Temporal-Boundary Era — `starting` and `until` connectives.
    # Quoted ISO 8601 date strings as inert metadata (compare=False).
    # `starting_date` is the effective date; `until_date` is the sunset.
    # Both None when no temporal boundary is declared. Evaluation is a
    # product-layer concern (Receipts server temporal_window field).
    starting_date: str | None = field(default=None, compare=False)
    until_date: str | None = field(default=None, compare=False)


@dataclass
class AboutNode(ASTNode):
    """Meta-Structural Era — program topic declaration.

    `about` is a declaration, not a verb. It declares the program's
    topic as inert metadata: visible to tooling (inspect, Receipts,
    Inyim, TUI header) but not stored in the symbol table and not
    executable. Single, first-line-only (MS-Q1).

    `topic` is the declared topic string. For quoted input
    (`about "expense authorization"`), it is the quoted content.
    For bare-word input (`about expense authorization`), it is the
    remaining tokens joined with spaces.
    """
    topic: str


# Set of operator words that may follow `is` as a comparison introducer.
_COMPARISON_OPERATORS = frozenset({"above", "below", "equal_to"})


# ---------------------------------------------------------------------------
# Internal exception
# ---------------------------------------------------------------------------


class _ParseError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


# ---------------------------------------------------------------------------
# TokenStream with peek/consume + clause-context stack (v1c §51)
# ---------------------------------------------------------------------------


class TokenStream:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self._clauses: list[str] = []

    def peek(self, offset: int = 0) -> Token | None:
        i = self.pos + offset
        return self.tokens[i] if 0 <= i < len(self.tokens) else None

    def consume(self) -> Token | None:
        if self.pos >= len(self.tokens):
            return None
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def push_clause(self, name: str) -> None:
        self._clauses.append(name)

    def pop_clause(self) -> None:
        self._clauses.pop()

    def in_clause(self, name: str) -> bool:
        return name in self._clauses


# ---------------------------------------------------------------------------
# Top-level entry
# ---------------------------------------------------------------------------


def parse(
    tokens: list[Token],
    composition_names: set[str] | None = None,
) -> ASTNode | LiminateResult:
    """Parse a canonically-ordered token list into an AST.

    Returns:
        - ASTNode on success.
        - LiminateResult with status AMBER_PRECEDENCE if a `where` clause
          uses both `and` and `or` (v1a §30). The pending AST is attached
          so the caller can resume after confirmation.
        - LiminateResult with status ERROR_PARSE on any other parse failure.
    """
    if not tokens:
        return LiminateResult(
            status=ResultStatus.ERROR_PARSE,
            message="There's nothing to parse here.",
            executed=False,
        )

    stream = TokenStream(tokens)
    comp = composition_names or set()

    try:
        ast = _parse_operation_sequence(stream, comp)
        if not stream.at_end():
            unexpected = stream.peek()
            raise _ParseError(
                f"I didn't expect '{unexpected.value}' here."
            )
    except _ParseError as e:
        return LiminateResult(
            status=ResultStatus.ERROR_PARSE,
            message=e.message,
            executed=False,
        )

    # v1a §30: mixed and/or in any `where` clause -> AMBER_PRECEDENCE.
    if _contains_mixed_precedence(ast):
        from .renderer import render, render_with_explicit_precedence
        return LiminateResult(
            status=ResultStatus.AMBER_PRECEDENCE,
            canonical=render(ast),
            message=(
                f"I'll read this as: {render_with_explicit_precedence(ast)}. "
                "Is that what you mean? If not, split it into two statements."
            ),
            executed=False,
            pending_ast=ast,
        )

    return ast


# ---------------------------------------------------------------------------
# Meta-Structural Era: `about` declaration
# ---------------------------------------------------------------------------


def parse_about(tokens: list[Token]) -> AboutNode | None:
    """Parse an `about` declaration from the first non-blank, non-comment
    line of a program.

    Returns AboutNode if the line is an `about` declaration, None if it
    is not (the line should then be fed to the normal parse pipeline).
    Raises _ParseError (surfaced as ERROR_PARSE by the caller) if the
    line starts with `about` but has malformed content.

    Design: single, first-line-only (MS-Q1). The CLI calls this on the
    first eligible line; if it returns an AboutNode, the line is consumed
    and not passed to the normal pipeline. If it returns None, the line
    is a normal statement.
    """
    if not tokens:
        return None
    if not (tokens[0].type is TokenType.DECLARATION and tokens[0].value == "about"):
        return None

    # `about` with no content is a parse error.
    if len(tokens) == 1:
        raise _ParseError(
            "'about' needs a topic — try: about \"expense authorization\" "
            "or about expense-authorization."
        )

    # Quoted string: `about "expense authorization"` — one QUOTED_STRING
    # token, nothing after it.
    if tokens[1].type is TokenType.QUOTED_STRING:
        if len(tokens) > 2:
            raise _ParseError(
                f"I didn't expect anything after the quoted topic in "
                f"'about'. Try: about \"{tokens[1].value}\"."
            )
        return AboutNode(topic=tokens[1].value)

    # Bare words: `about expense authorization` — join remaining tokens.
    # All token types are accepted (UNKNOWN, NUMBER, etc.) and joined
    # with spaces. Reserved words in this position are allowed — they
    # are being used as topic words, not as Liminate syntax.
    words = [t.value for t in tokens[1:]]
    return AboutNode(topic=" ".join(words))


# ---------------------------------------------------------------------------
# v3a §108–§110: `when` block parsing
# ---------------------------------------------------------------------------


def parse_when_block(
    header_tokens: list[Token],
    action_token_lists: list[list[Token]],
    composition_names: set[str] | None = None,
) -> ASTNode | LiminateResult:
    """Parse a `when <cond> [unless <guard>] [:]` header plus its
    indented action block (v3a §108/§109/§110).

    `header_tokens` is the reordered token sequence for the `when` line
    (must begin with the `when` connective). `action_token_lists` is one
    reordered token list per indented action line; blank lines have been
    elided by the caller (v1c §48 / v3a §110). Indentation has already
    been validated at the CLI boundary — `parse_when_block` itself does
    not see leading whitespace.

    Returns:
        - WhenNode on success.
        - LiminateResult AMBER_PRECEDENCE if any condition or action
          sub-statement contains mixed `and`/`or` (v3a §123).
        - LiminateResult ERROR_PARSE on grammar errors.
    """
    if not header_tokens:
        return LiminateResult(
            status=ResultStatus.ERROR_PARSE,
            message="There's nothing to parse here.",
            executed=False,
        )

    # Meta-Structural Era batch 3 — `inherited when` support. A
    # statement-initial `inherited` operator precedes the `when`
    # connective; strip it here and flag the resulting WhenNode so the
    # rest of the header parses exactly as a plain `when` block.
    is_inherited = False
    if (
        header_tokens[0].type is TokenType.OPERATOR
        and header_tokens[0].value == "inherited"
    ):
        is_inherited = True
        header_tokens = header_tokens[1:]

    if not header_tokens:
        return LiminateResult(
            status=ResultStatus.ERROR_PARSE,
            message=(
                "'inherited' must be followed by a 'when' statement here."
            ),
            executed=False,
        )

    if not (
        header_tokens[0].type is TokenType.CONNECTIVE
        and header_tokens[0].value == "when"
    ):
        return LiminateResult(
            status=ResultStatus.ERROR_PARSE,
            message=(
                f"I expected a 'when' statement here, not "
                f"'{header_tokens[0].value}'."
            ),
            executed=False,
        )

    # v3a §110: an empty action block is a parse error. The header alone
    # has no executable body.
    if not action_token_lists:
        return LiminateResult(
            status=ResultStatus.ERROR_PARSE,
            message=(
                "'when' needs an indented action block — at least one "
                "line after the 'when' line, indented by at least one "
                "space (v3a §110)."
            ),
            executed=False,
        )

    comp = composition_names or set()

    # Parse the header — condition + optional unless guard + optional `:`.
    stream = TokenStream(header_tokens[1:])  # skip the `when` connective
    inherited_from: str | None = None
    try:
        if stream.at_end():
            raise _ParseError(
                "I expected a condition after 'when'. "
                "Try: when <name> is above <value>."
            )
        condition = _parse_or_condition(stream)

        unless_guard: ASTNode | None = None
        peek = stream.peek()
        if (
            peek
            and peek.type is TokenType.CONNECTIVE
            and peek.value == "unless"
        ):
            stream.consume()  # eat `unless`
            if stream.at_end():
                raise _ParseError(
                    "I expected a guard condition after 'unless'."
                )
            unless_guard = _parse_or_condition(stream)

        # Meta-Structural Era — `inherited when ... from <agent>` agent
        # attribution (Invariant Checkpoint v2 §43). Legal only with the
        # `inherited` prefix. By this point the condition and optional
        # guard are fully parsed, and no production in the when-condition
        # grammar consumes `from`, so a `from` here is unambiguously
        # attribution.
        if is_inherited:
            inherited_from = _try_consume_inherited_from(stream)
        else:
            peek = stream.peek()
            if (
                peek
                and peek.type is TokenType.CONNECTIVE
                and peek.value == "from"
            ):
                raise _ParseError(
                    "'from' attribution on a 'when' header needs the "
                    "'inherited' prefix — try: inherited when <condition> "
                    "from <agent-name>."
                )

        # v3a §110: the colon after the `when` line is optional.
        peek = stream.peek()
        if peek and peek.type is TokenType.DELIMITER and peek.value == ":":
            stream.consume()

        if not stream.at_end():
            unexpected = stream.peek()
            raise _ParseError(
                f"I didn't expect '{unexpected.value}' in the 'when' header."
            )
    except _ParseError as e:
        return LiminateResult(
            status=ResultStatus.ERROR_PARSE,
            message=e.message,
            executed=False,
        )

    # Parse each action line through the regular `parse()` path so all
    # existing grammar (compositions, choose, each, etc.) applies. Inside
    # `_parse_one_operation`, `when` / `unless` are rejected with v3a
    # error wording; `finish` is parsed as a regular verb.
    action_asts: list[ASTNode] = []
    for tokens in action_token_lists:
        sub = parse(tokens, composition_names=comp)
        if isinstance(sub, LiminateResult):
            # Propagate parse / amber outcomes directly. Amber from an
            # action statement still blocks Phase 2 per v3a §107.
            return sub
        action_asts.append(sub)

    action: ASTNode = (
        action_asts[0] if len(action_asts) == 1
        else SequenceNode(operations=action_asts)
    )

    when_node = WhenNode(condition=condition, unless=unless_guard, action=action)
    if is_inherited:
        when_node.inherited = True
        # Invariant Checkpoint v2 §43 — statement-final agent attribution
        # extended to `inherited when` headers. Flows into HANDLER_FIRE
        # trigger metadata via listener._wrap_with_trigger.
        when_node.inherited_from = inherited_from

    # v3a §123: condition or guard mixed and/or — amber. Action sub-
    # statements were already amber-checked individually by `parse()`,
    # which would have short-circuited above. The check here is for the
    # header's two condition ASTs.
    if _contains_mixed_precedence(when_node):
        from .renderer import render, render_with_explicit_precedence
        return LiminateResult(
            status=ResultStatus.AMBER_PRECEDENCE,
            canonical=render(when_node),
            message=(
                f"I'll read this as: "
                f"{render_with_explicit_precedence(when_node)}. "
                "Is that what you mean? If not, split it into two statements."
            ),
            executed=False,
            pending_ast=when_node,
        )

    return when_node


# ---------------------------------------------------------------------------
# Operation sequencing (`and` between complete verb phrases, §21 rule 3)
# ---------------------------------------------------------------------------


def _starts_operation(tok: Token | None) -> bool:
    """True if `tok` can begin a sequenced operation — a verb, or the
    statement-initial `inherited` operator (Meta-Structural Era batch 3),
    which is followed by its own verb."""
    if tok is None:
        return False
    if tok.type is TokenType.VERB:
        return True
    return tok.type is TokenType.OPERATOR and tok.value == "inherited"


def _parse_operation_sequence(stream: TokenStream, comp: set[str]) -> ASTNode:
    first = _parse_one_operation(stream, comp)
    operations: list[ASTNode] = [first]
    connectors: list[str] = []
    while not stream.at_end():
        peek = stream.peek()
        if peek is None or peek.type is not TokenType.CONNECTIVE:
            break
        if peek.value == "and":
            nxt = stream.peek(1)
            if not _starts_operation(nxt):
                # `and` followed by a non-verb means we're not sequencing
                # operations (could be a condition continuation handled
                # elsewhere). Stop the loop and let the caller decide.
                break
            stream.consume()  # eat `and`
            connectors.append("and")
            operations.append(_parse_one_operation(stream, comp))
        elif peek.value == "then":
            # Normative Era batch 2: `then` always sequences operations;
            # the next token must be a verb (or an `inherited` verb). Unlike
            # `and`, `then` has no other meaning, so anything else is a hard
            # parse error.
            nxt = stream.peek(1)
            if not _starts_operation(nxt):
                raise _ParseError(
                    "I expected a verb after 'then'. "
                    "Try: <action> then <next-action>."
                )
            stream.consume()  # eat `then`
            connectors.append("then")
            operations.append(_parse_one_operation(stream, comp))
        else:
            break
    if len(operations) == 1:
        return operations[0]
    return SequenceNode(operations=operations, connectors=connectors)


def _try_consume_starting_until(
    stream: TokenStream,
) -> tuple[str | None, str | None]:
    """Consume optional `starting "<date>"` and/or `until "<date>"`
    clauses at statement-initial position (Temporal-Boundary Era, DT-Q4).

    Returns (starting_date, until_date). Either or both may be None.
    Raises _ParseError if `starting`/`until` is present but not followed
    by a quoted string, or if the quoted string is not valid ISO 8601.

    Canonical order: `starting` before `until`. Both before `inherited`.
    A reversed `until ... starting ...` consumes `until` only; the
    trailing `starting` is left in the stream and errors on the verb —
    canonical order is enforced by grammar, not by an explicit message.
    """
    starting_date: str | None = None
    until_date: str | None = None

    peek = stream.peek()
    if (
        peek
        and peek.type is TokenType.CONNECTIVE
        and peek.value == "starting"
    ):
        stream.consume()  # eat `starting`
        date_tok = stream.consume()
        if date_tok is None or date_tok.type is not TokenType.QUOTED_STRING:
            got = date_tok.value if date_tok else "end of line"
            raise _ParseError(
                f"'starting' needs a quoted date — try: "
                f'starting "2025-07-01". Got: {got}.'
            )
        _validate_iso_date(date_tok.value, "starting")
        starting_date = date_tok.value

    peek = stream.peek()
    if (
        peek
        and peek.type is TokenType.CONNECTIVE
        and peek.value == "until"
    ):
        stream.consume()  # eat `until`
        date_tok = stream.consume()
        if date_tok is None or date_tok.type is not TokenType.QUOTED_STRING:
            got = date_tok.value if date_tok else "end of line"
            raise _ParseError(
                f"'until' needs a quoted date — try: "
                f'until "2025-12-31". Got: {got}.'
            )
        _validate_iso_date(date_tok.value, "until")
        until_date = date_tok.value

    return starting_date, until_date


def _validate_iso_date(date_str: str, keyword: str) -> None:
    """Validate that a date string is ISO 8601 format (YYYY-MM-DD).

    Raises _ParseError with a helpful message if the format is wrong.
    Does NOT validate that the date is a real calendar date (e.g.
    2025-02-30 passes format validation but is not a real date) —
    that's a runtime concern if needed later. The parser only checks
    the structural format.
    """
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        raise _ParseError(
            f"'{keyword}' needs an ISO 8601 date (YYYY-MM-DD) — "
            f'try: {keyword} "2025-07-01". Got: "{date_str}".'
        )


def _try_consume_because(stream: TokenStream) -> str | None:
    """Consume an optional `because "<rationale>"` clause at the end of a
    verb statement (Meta-Structural Era batch 2, MS-Q2).

    `because` is statement-terminal: it attaches a quoted rationale to the
    immediately-preceding verb statement as inert metadata. Returns the
    rationale string if `because` is present, None otherwise. Raises
    _ParseError if `because` is present but not followed by a quoted
    string — bare words and numbers are rejected because rationales are
    natural-language prose that may contain reserved words.
    """
    peek = stream.peek()
    if not (
        peek
        and peek.type is TokenType.CONNECTIVE
        and peek.value == "because"
    ):
        return None
    stream.consume()  # eat `because`
    rationale_tok = stream.consume()
    if rationale_tok is None or rationale_tok.type is not TokenType.QUOTED_STRING:
        got = rationale_tok.value if rationale_tok else "end of line"
        raise _ParseError(
            f"'because' needs a quoted rationale — try: "
            f'because "your reason here". Got: {got}.'
        )
    return rationale_tok.value


def _try_consume_unless_exception(stream: TokenStream) -> ASTNode | None:
    """v28 — consume an optional `unless <condition>` exception clause
    immediately following a deontic verb's main condition.

    Shared by `_parse_require`, `_parse_forbid`, `_parse_permit`, and
    `_parse_expect`. Mirrors the `unless` guard consumption in
    `parse_when_block` — same token shape, different grammatical
    position (inside the verb's condition grammar rather than a `when`
    header). Returns the exception condition AST, or None if no
    `unless` is present.
    """
    peek = stream.peek()
    if not (
        peek
        and peek.type is TokenType.CONNECTIVE
        and peek.value == "unless"
    ):
        return None
    stream.consume()  # eat `unless`
    if stream.at_end():
        raise _ParseError("I expected a condition after 'unless'.")
    return _parse_or_condition(stream)


def _try_consume_inherited_from(stream: TokenStream) -> str | None:
    """Consume an optional `from <agent-name>` attribution at the end of
    an `inherited` statement (Meta-Structural Era batch 3, MS-Q4).

    Returns the agent name string if `from` attribution is present, None
    otherwise. Only called on `inherited` statements — on non-inherited
    statements, a trailing `from` belongs to other grammatical roles
    (remember-copy semantics, gather range, remove source, composition
    argument) and is left untouched here.

    The agent name is a single UNKNOWN token (a hyphenated name like
    `agent-compliance`). Quoted strings and reserved words are rejected.
    """
    peek = stream.peek()
    if not (
        peek
        and peek.type is TokenType.CONNECTIVE
        and peek.value == "from"
    ):
        return None
    stream.consume()  # eat `from`
    agent_tok = stream.consume()
    if agent_tok is None:
        raise _ParseError(
            "'from' in an inherited statement needs an agent name — "
            "try: inherited <verb> ... from <agent-name>."
        )
    if agent_tok.type is TokenType.QUOTED_STRING:
        raise _ParseError(
            f"Agent names can't have spaces. Try a hyphenated name "
            f"like '{_hyphenate(agent_tok.value)}' instead."
        )
    if agent_tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(agent_tok.value)
        if cat:
            raise _ParseError(
                f"The word '{agent_tok.value}' is reserved in Liminate "
                f"— it's used as a {cat}. Please use a name for the "
                f"agent, like 'agent-compliance'."
            )
        raise _ParseError(
            f"I expected an agent name after 'from', not "
            f"'{agent_tok.value}'."
        )
    return agent_tok.value


def _parse_one_operation(stream: TokenStream, comp: set[str]) -> ASTNode:
    # Statement-initial `starting`/`until` temporal modifiers
    # (Temporal-Boundary Era, DT-Q4). Consumed before `inherited` so the
    # canonical order is `starting ... until ... inherited <verb> ...`.
    # The dates are attached to the resulting node after the verb is parsed.
    starting_date, until_date = _try_consume_starting_until(stream)

    # Statement-initial `inherited` modifier (Meta-Structural Era batch 3).
    # Marks the statement as carried forward from a prior context. The flag
    # is set on the resulting node after the verb + slots are parsed.
    is_inherited = False
    peek = stream.peek()
    if (
        peek
        and peek.type is TokenType.OPERATOR
        and peek.value == "inherited"
    ):
        stream.consume()  # eat `inherited`
        is_inherited = True

    # Parse the operation itself, then consume an optional statement-terminal
    # `because "<rationale>"` clause (MS-Q2). Routing the rationale through
    # this single chokepoint attaches it to the last-parsed statement node
    # in every context — top-level, `and`/`then` sequences, `choose`
    # branches, and `each` bodies — without per-verb plumbing.
    node = _parse_one_operation_inner(stream, comp)
    rationale = _try_consume_because(stream)
    if rationale is not None:
        node.rationale = rationale

    # Statement-final `from <agent>` attribution (MS-Q4) — scoped to
    # `inherited` statements only. Canonical order is
    # `inherited <verb> <slots> because "<rationale>" from <agent>`: by the
    # time we get here the verb parser has already consumed any `from` that
    # belongs to a slot (remember-copy, gather, remove, composition arg), so
    # the only `from` left is the attribution.
    if is_inherited:
        node.inherited = True
        node.inherited_from = _try_consume_inherited_from(stream)

    # Attach temporal-boundary metadata (Temporal-Boundary Era). Inert —
    # never read by execution; rendered in canonical order by the renderer.
    if starting_date is not None:
        node.starting_date = starting_date
    if until_date is not None:
        node.until_date = until_date
    return node


def _parse_one_operation_inner(stream: TokenStream, comp: set[str]) -> ASTNode:
    t = stream.peek()
    if t is None:
        raise _ParseError("I expected an operation here.")
    if t.type is TokenType.VERB:
        return _parse_verb_statement(stream, comp)
    if t.type is TokenType.UNKNOWN:
        # v1b §41 fallback: named composition call.
        if t.value in comp:
            stream.consume()
            # v2d §96: `<comp-name> from <name>` at top-level is parameter
            # passing. This supersedes the v2a §70 composition-chaining
            # error — the from-after-comp shape is now resolved syntax.
            after = stream.peek()
            if after and after.type is TokenType.CONNECTIVE and after.value == "from":
                stream.consume()  # eat `from`
                arg = _consume_parameter_arg(stream, comp_name=t.value)
                return CompositionCallNode(name=t.value, arg=arg)
            return CompositionCallNode(name=t.value)
        # v25 — tombstoned words (renamed verbs) lex as UNKNOWN, since
        # they're in no TokenType category table. Give the rename-specific
        # error before the generic "I don't recognize a command" fallback.
        if t.value in TOMBSTONES:
            raise _ParseError(
                f"The word '{t.value}' was renamed — use '{TOMBSTONES[t.value]}'."
            )
        raise _ParseError(
            "I don't recognize a command here. Every sentence needs a verb "
            "like 'remember', 'show', 'filter', 'count', 'gather', "
            "'sum', 'each', or 'choose'."
        )
    # v3a §108: `when` is a top-level statement only. Any `when` reaching
    # this code path is inside a composition body, an `each` body, or a
    # `when` action block — all forbidden.
    if t.type is TokenType.CONNECTIVE and t.value == "when":
        raise _ParseError(
            "'when' is a top-level statement and starts its own indented "
            "action block. It can't appear inside compositions, 'each' "
            "bodies, or another 'when' action block."
        )
    # v3a §109: `unless` is a guard clause on `when`, never standalone.
    if t.type is TokenType.CONNECTIVE and t.value == "unless":
        raise _ParseError(
            "'unless' is a guard clause that follows a 'when' condition — "
            "it can't introduce a statement on its own. "
            "Try: when <condition> unless <guard>."
        )
    # Meta-structural: declarations are first-line-only and handled by
    # the CLI before the normal pipeline. If `about` reaches here, it
    # means it appeared on a non-first line.
    if t.type is TokenType.DECLARATION:
        raise _ParseError(
            f"'{t.value}' is a declaration that must be the first line "
            f"of the program (after any comments). It can't appear here."
        )
    raise _ParseError(f"I didn't expect '{t.value}' at the start of an operation.")


def _parse_verb_statement(stream: TokenStream, comp: set[str]) -> ASTNode:
    verb = stream.consume()
    if verb.value == "remember":
        return _parse_remember(stream, comp)
    if verb.value == "show":
        # v2a §69 (D1): multi-field display is only valid as the body of
        # an `each` loop. The parser tracks that via clause context.
        return _parse_show(stream, in_each=stream.in_clause("each"))
    if verb.value == "filter":
        return _parse_filter(stream)
    if verb.value == "keep":
        return _parse_keep(stream)
    if verb.value == "count":
        return _parse_count(stream)
    if verb.value == "gather":
        return _parse_gather(stream)
    if verb.value == "sum":
        return _parse_sum(stream)
    if verb.value == "each":
        return _parse_each(stream, comp)
    if verb.value == "choose":
        # v2d §102 — `choose` inside `each` is deferred. Reject at parse
        # time with the spec-mandated wording (sentence 94 / Outcome 4).
        if stream.in_clause("each"):
            raise _ParseError(
                "'choose' can't appear inside 'each'. To handle items "
                "differently, use 'keep' to separate them by condition."
            )
        return _parse_choose(stream, comp)
    if verb.value == "add":
        return _parse_add(stream)
    if verb.value == "remove":
        return _parse_remove(stream)
    if verb.value == "weakens":
        return _parse_weakens(stream)
    if verb.value == "require":
        return _parse_require(stream)
    if verb.value == "forbid":
        return _parse_forbid(stream)
    if verb.value == "permit":
        return _parse_permit(stream)
    if verb.value == "assign":
        return _parse_assign(stream)
    if verb.value == "expect":
        return _parse_expect(stream)
    if verb.value == "sort":
        return _parse_sort(stream)
    if verb.value == "compare":
        return _parse_compare(stream)
    if verb.value == "transform":
        return _parse_transform(stream)
    if verb.value == "finish":
        # v3a §112 — slot-less verb. Phase 1 semantic check (in the
        # analyzer) rejects calls outside an action-block context; here
        # we just parse the leaf node. `finish` may legitimately appear
        # in composition bodies (analyzer defers the error to call time).
        return FinishNode()
    # v4a §137 — pack-defined verb dispatch comes after the base verbs.
    pack_sig = get_active_pack_verb(verb.value)
    if pack_sig is not None:
        return _parse_pack_verb(stream, pack_sig)
    raise _ParseError(f"Unknown verb '{verb.value}'.")


# ---------------------------------------------------------------------------
# v4a §137 — pack verb parsing
# ---------------------------------------------------------------------------


def _parse_pack_verb(
    stream: TokenStream, sig: PackVerbSignature,
) -> PackVerbNode:
    """Fill the pack verb's slots in source order.

    v2 (pack verb contract extension):
    - Positional slots (`connective is None`) consume the next value
      token directly. `value_type` determines what's accepted.
    - Connective-introduced slots peek for the connective; if found,
      consume it then the value per `value_type`.
    - `value_type == "value"` routes through `_parse_value` (NUMBER,
      UNKNOWN, QUOTED_STRING, FieldAccessNode).
    - `value_type == "name"` consumes a single UNKNOWN as NameRef.
    """
    slot_values: dict[str, ASTNode] = {}
    for slot in sig.slots:
        if slot.connective is None:
            # Positional slot — consume value directly.
            peek = stream.peek()
            if peek is None:
                if slot.required:
                    raise _ParseError(
                        _pack_verb_missing_slot_error(sig, slot)
                    )
                continue
            slot_values[slot.name] = _parse_pack_slot_value(stream, sig, slot)
            continue
        # Connective-introduced slot.
        peek = stream.peek()
        if not (
            peek
            and peek.type is TokenType.CONNECTIVE
            and peek.value == slot.connective
        ):
            if slot.required:
                raise _ParseError(_pack_verb_missing_slot_error(sig, slot))
            continue
        stream.consume()  # eat the connective
        if stream.peek() is None:
            raise _ParseError(_pack_verb_missing_slot_error(sig, slot))
        slot_values[slot.name] = _parse_pack_slot_value(stream, sig, slot)
    return PackVerbNode(word=sig.word, signature=sig, slot_values=slot_values)


def _parse_pack_slot_value(
    stream: TokenStream, sig: PackVerbSignature, slot,
) -> ASTNode:
    """v2 — consume one slot value per the slot's `value_type`."""
    if slot.value_type == "value":
        return _parse_value(stream)
    # "name" mode — UNKNOWN-only path.
    # Phase 3 Spec 2 (iterable pack verbs): inside an `each` block, the
    # `each` pronoun is a valid slot filler — it resolves to the current
    # element during per-element execution. Mirrors the `transform`
    # precedent in `_parse_atom`. Without the enclosing `each`, `each`
    # falls through to the reserved-word rejection below.
    peek = stream.peek()
    if (
        peek is not None
        and peek.type is TokenType.VERB
        and peek.value == "each"
        and stream.in_clause("each")
    ):
        stream.consume()  # eat the `each` pronoun
        return EachPronoun()
    value_tok = stream.consume()
    if value_tok is None:
        raise _ParseError(_pack_verb_missing_slot_error(sig, slot))
    if value_tok.type is TokenType.QUOTED_STRING:
        raise _ParseError(
            f"Names can't have spaces. Try a hyphenated name like "
            f"'{_hyphenate(value_tok.value)}' instead."
        )
    if value_tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(value_tok.value)
        if cat:
            raise _ParseError(
                f"The word '{value_tok.value}' is reserved in Liminate "
                f"— it's used as a {cat}. Please use a name you've "
                f"created."
            )
        intro = (
            f"after '{sig.word} {slot.connective}'"
            if slot.connective is not None
            else f"after '{sig.word}'"
        )
        raise _ParseError(
            f"I expected a name {intro}, not '{value_tok.value}'."
        )
    return NameRef(name=value_tok.value)


def _pack_verb_missing_slot_error(
    sig: PackVerbSignature, slot,
) -> str:
    """Generate the missing-slot error for a pack verb. v2: positional
    slots describe themselves by name + type_constraint; connective-
    introduced slots use the existing `<verb> <connective> <target>`
    phrasing."""
    constraint = slot.type_constraint or "value"
    if slot.connective is None:
        # Positional slot. Build an example from the rest of the signature.
        rest_example = ""
        for other in sig.slots:
            if other is slot or other.connective is None:
                continue
            other_constraint = other.type_constraint or "value"
            rest_example += f" {other.connective} <{other_constraint}-name>"
        role = "text value" if slot.value_type == "value" else "name"
        placeholder = (
            f'"<{slot.name}>"' if slot.value_type == "value"
            else f"<{slot.name}>"
        )
        return (
            f"'{sig.word}' needs a {role} for '{slot.name}' — try: "
            f"{sig.word} {placeholder}{rest_example}."
        )
    role = "destination" if slot.connective == "to" else slot.name
    return (
        f"'{sig.word}' needs a {role} — try: "
        f"{sig.word} {slot.connective} <{constraint}-name>."
    )


# ---------------------------------------------------------------------------
# remember
# ---------------------------------------------------------------------------


def _parse_remember(stream: TokenStream, comp: set[str]) -> ASTNode:
    """remember <body>, where <body> is one of:
        how to <name> : <statement>             (composition definition)
        <article>? <descriptor>* called <name> with <value-expr>
        <article>? <descriptor>* called <name> with <list-construct>
        <article>? <descriptor>* called <name> with <record-fields>
        <article>? <descriptor>* called <name> from <name>
        <article>? <descriptor>* called <name> from <verb-phrase>
    """
    peek = stream.peek()
    if peek and peek.type is TokenType.CONNECTIVE and peek.value == "how":
        return _parse_composition_definition(stream, comp)

    descriptor, saw_list = _consume_remember_intro(stream)

    called = stream.consume()
    if not (called and called.type is TokenType.CONNECTIVE and called.value == "called"):
        raise _ParseError(
            "I expected the word 'called' to introduce the name."
        )

    name = _consume_name(stream, after="'called'")

    intro = stream.consume()
    if intro is None:
        if saw_list:
            return RememberListNode(name=name, items=[], descriptor=descriptor)
        raise _ParseError(f"I expected 'with' or 'from' after '{name}'.")
    if intro.type is not TokenType.CONNECTIVE or intro.value not in ("with", "from"):
        raise _ParseError(f"I expected 'with' or 'from', not '{intro.value}'.")

    if intro.value == "with":
        return _parse_remember_with(stream, name, descriptor, saw_list)
    return _parse_remember_from(stream, name, comp, descriptor)


def _parse_composition_definition(stream: TokenStream, comp: set[str]) -> RememberCompositionNode:
    stream.consume()  # how
    to = stream.consume()
    if not (to and to.type is TokenType.CONNECTIVE and to.value == "to"):
        raise _ParseError("I expected 'to' after 'how'.")

    name = _consume_name(stream, after="'how to'")

    # v2d §96 — optional `from <param-name>` between the composition name
    # and the colon. Reserved-word exclusion (v1a §29) is enforced via
    # _consume_name. Single parameter only; a second `from` (or any
    # token between the parameter and the colon) is a parse error.
    param: str | None = None
    peek = stream.peek()
    if peek and peek.type is TokenType.CONNECTIVE and peek.value == "from":
        stream.consume()  # eat `from`
        param = _consume_name(stream, after=f"'from' in composition '{name}'")

    colon = stream.consume()
    if not (colon and colon.type is TokenType.DELIMITER and colon.value == ":"):
        raise _ParseError("I expected ':' after the composition name.")

    body = _parse_operation_sequence(stream, comp)
    return RememberCompositionNode(name=name, body=body, param=param)


def _consume_remember_intro(stream: TokenStream) -> tuple[str | None, bool]:
    """Consume zero+ articles and zero+ descriptor UNKNOWNs before `called`.

    Returns a tuple of (descriptor, saw_list):
      - descriptor: the verbatim sequence of descriptor words the user
        wrote between the article and `called`, joined by spaces; None
        if no descriptor was present. Preserved for canonical rendering
        per v2a §71 (D6) — descriptors remain semantically decorative
        (v1b §36) but are now rendered back to the user.
      - saw_list: True if the descriptor sequence contains the word
        `list` (forces singleton-list construction in
        `_parse_remember_with` so `remember a list called orders with
        order1` produces a 1-item list, not a flat value — see v1d §65
        sentence 38).
    """
    parts: list[str] = []
    saw_list = False
    while True:
        t = stream.peek()
        if t is None:
            raise _ParseError("I expected 'called' to introduce the name.")
        if t.type is TokenType.CONNECTIVE and t.value == "called":
            return (" ".join(parts) if parts else None, saw_list)
        if t.type is TokenType.ARTICLE:
            stream.consume()
            continue
        if t.type is TokenType.UNKNOWN:
            parts.append(t.value)
            if t.value == "list":
                saw_list = True
            stream.consume()
            continue
        # Vocabulary word at a position that should have been a descriptor.
        cat = reserved_category(t.value)
        if cat:
            raise _ParseError(
                f"The word '{t.value}' is reserved in Liminate — "
                f"it's used as a {cat}. Please choose a different name."
            )
        raise _ParseError(f"I didn't expect '{t.value}' before 'called'.")


def _parse_remember_with(
    stream: TokenStream, name: str, descriptor: str | None, saw_list: bool,
) -> ASTNode:
    first = stream.peek()
    if first is None:
        raise _ParseError(f"I expected a value after 'with'.")
    second = stream.peek(1)

    # Record path: first token is UNKNOWN (field name) and second is `as`.
    if (
        first.type is TokenType.UNKNOWN
        and second is not None
        and second.type is TokenType.CONNECTIVE
        and second.value == "as"
    ):
        stream.push_clause("with_as")
        try:
            fields = _parse_record_fields(stream)
        finally:
            stream.pop_clause()
        return RememberRecordNode(name=name, fields=fields, descriptor=descriptor)

    # Otherwise: value, possibly followed by `and <value>` for list construction.
    stream.push_clause("with")
    try:
        first_value = _parse_value(stream)
        items = [first_value]
        is_list = False
        while True:
            peek = stream.peek()
            if not (peek and peek.type is TokenType.CONNECTIVE and peek.value == "and"):
                break
            nxt = stream.peek(1)
            if nxt and nxt.type is TokenType.VERB:
                break  # operation sequencing — return to top-level
            stream.consume()
            items.append(_parse_value(stream))
            is_list = True
    finally:
        stream.pop_clause()

    if is_list or saw_list:
        return RememberListNode(name=name, items=items, descriptor=descriptor)
    return RememberValueNode(name=name, value=items[0], descriptor=descriptor)


def _parse_record_fields(stream: TokenStream) -> list[tuple[str, ASTNode]]:
    fields: list[tuple[str, ASTNode]] = []
    fields.append(_parse_record_field(stream))
    while True:
        peek = stream.peek()
        if not (peek and peek.type is TokenType.CONNECTIVE and peek.value == "and"):
            break
        nxt = stream.peek(1)
        if nxt and nxt.type is TokenType.VERB:
            break  # operation sequencing
        stream.consume()  # eat `and`
        fields.append(_parse_record_field(stream))
    return fields


def _parse_record_field(stream: TokenStream) -> tuple[str, ASTNode]:
    field_tok = stream.consume()
    if field_tok is None:
        raise _ParseError("I expected a field name.")
    if field_tok.type is TokenType.QUOTED_STRING:
        # v2c §87 — field names can't be quoted (no spaces).
        raise _ParseError(
            f"Field names can't have spaces. Try a hyphenated name like "
            f"'{_hyphenate(field_tok.value)}' instead."
        )
    if field_tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(field_tok.value)
        if cat:
            raise _ParseError(
                f"The word '{field_tok.value}' is reserved in Liminate — "
                f"it's used as a {cat}. Please choose a different name."
            )
        raise _ParseError(f"I expected a field name, not '{field_tok.value}'.")
    field_name = field_tok.value

    as_tok = stream.consume()
    if not (as_tok and as_tok.type is TokenType.CONNECTIVE and as_tok.value == "as"):
        # The user wrote `<field>` without `as <value>`.
        raise _ParseError(
            f"I expected a value after '{field_name}'. "
            f"Try: '{field_name} as [value]'."
        )

    value = _parse_value(stream)
    return field_name, value


def _parse_remember_from(
    stream: TokenStream, name: str, comp: set[str], descriptor: str | None = None,
) -> ASTNode:
    """`from` in `remember` (v1b §43):
       next token is VERB        -> result capture via recursive descent
       next token is a known comp -> composition call (with optional param)
       otherwise                 -> value expression, which may include
                                    arithmetic (Infrastructure Era)
    """
    peek = stream.peek()
    if peek is None:
        raise _ParseError("I expected an expression after 'from'.")
    if peek.type is TokenType.VERB:
        sub = _parse_verb_statement(stream, comp)
        return RememberValueNode(name=name, value=sub, descriptor=descriptor)
    if peek.type is TokenType.UNKNOWN and peek.value in comp:
        # v1b §41 + v2d §98 — named composition call as value expression.
        stream.consume()
        after = stream.peek()
        if after and after.type is TokenType.CONNECTIVE and after.value == "from":
            stream.consume()  # eat inner `from`
            arg = _consume_parameter_arg(stream, comp_name=peek.value)
            return RememberValueNode(
                name=name,
                value=CompositionCallNode(name=peek.value, arg=arg),
                descriptor=descriptor,
            )
        return RememberValueNode(
            name=name,
            value=CompositionCallNode(name=peek.value),
            descriptor=descriptor,
        )
    # Value expression — numbers, names (as NameRef per `from` semantics),
    # field access via `of`, or arithmetic expressions over any of those.
    value = _parse_value(stream)
    value = _name_ref_for_from(value)
    return RememberValueNode(name=name, value=value, descriptor=descriptor)


def _name_ref_for_from(node: ASTNode) -> ASTNode:
    """`from` copy-semantics: a bare UNKNOWN after `from` is a reference
    to a remembered symbol (NameRef errors if missing), not a string
    literal fallback (BareWord). Convert single BareWord values to
    NameRef, and recurse into ArithmeticNode operands so arithmetic
    operands also obey from-strictness."""
    if isinstance(node, BareWord):
        return NameRef(name=node.word)
    if isinstance(node, ArithmeticNode):
        return ArithmeticNode(
            left=_name_ref_for_from(node.left),
            right=_name_ref_for_from(node.right),
            op=node.op,
        )
    return node


# ---------------------------------------------------------------------------
# show / count / sum
# ---------------------------------------------------------------------------


def _parse_show(stream: TokenStream, *, in_each: bool = False) -> ShowNode:
    _consume_optional_article(stream)
    peek = stream.peek()
    # An optional target — if missing or followed by a sequencing `and verb`,
    # `show` displays the current iterator item (v1c §49).
    if peek is None:
        return ShowNode(target=None)
    if peek.type is TokenType.CONNECTIVE and peek.value == "and":
        nxt = stream.peek(1)
        if nxt and nxt.type is TokenType.VERB:
            return ShowNode(target=None)
    # v25 VW-Q2 — `show highest of nums` / `show highest total of orders`.
    if peek.type is TokenType.OPERATOR and peek.value in ("highest", "lowest"):
        return ShowNode(target=_parse_extrema(stream))
    if peek.type is TokenType.QUOTED_STRING:
        # v2c §87/§88 — `show "text"` is literal display. But if followed
        # by `of`, the user wrote a quoted field name (rejected). And
        # inside `each ... show`, a quoted target is also intended as a
        # field name (rejected by the same rule).
        stream.consume()
        after = stream.peek()
        if after and after.type is TokenType.CONNECTIVE and after.value == "of":
            rec_peek = stream.peek(1)
            rec = (
                rec_peek.value
                if rec_peek and rec_peek.type is TokenType.UNKNOWN
                else "<record>"
            )
            raise _ParseError(
                f"Field names can't have spaces. Try "
                f"'show {_hyphenate(peek.value)} of {rec}' instead."
            )
        if in_each:
            raise _ParseError(
                f"Field names can't have spaces. Try a hyphenated name "
                f"like '{_hyphenate(peek.value)}' instead."
            )
        # v2c §88 — literal display target carried into the AST.
        return ShowNode(target=QuotedString(content=peek.value))
    if peek.type is TokenType.UNKNOWN:
        stream.consume()
        # v2a §68 (D4) — `show <field> of <record>` accesses a single
        # field of a single record. The first unknown is interpreted as
        # the *field name* when `of` follows.
        after = stream.peek()
        if after and after.type is TokenType.CONNECTIVE and after.value == "of":
            stream.consume()  # eat `of`
            rec_tok = stream.consume()
            if rec_tok is None:
                raise _ParseError("I expected a record name after 'of'.")
            if rec_tok.type is not TokenType.UNKNOWN:
                rcat = reserved_category(rec_tok.value)
                if rcat:
                    raise _ParseError(
                        f"The word '{rec_tok.value}' is reserved in "
                        f"Liminate — it's used as a {rcat} and can't be "
                        f"used as a record name."
                    )
                raise _ParseError(
                    f"I expected a record name after 'of', not "
                    f"'{rec_tok.value}'."
                )
            # v2b §77 sub-decision I: chained `of` is a parse error
            # (no nested records in v2b).
            chain = stream.peek()
            if chain and chain.type is TokenType.CONNECTIVE and chain.value == "of":
                raise _ParseError(
                    "Field access uses one record at a time: "
                    "<field> of <record>. Chained forms (a of b of c) "
                    "need nested records, which v2b doesn't yet have."
                )
            return ShowNode(
                target=NameRef(name=peek.value),
                record_name=rec_tok.value,
            )
        # v2a §69 (D1) — multi-field display inside `each ... show`.
        # Within an `each` body, `and <field>` after the first field
        # name collects additional fields rather than starting a new
        # operation (the four pre-existing `and` meanings in §21 don't
        # claim this slot; v2a §69 adds the fifth).
        if in_each:
            extras: list[str] = []
            while True:
                ap = stream.peek()
                if not (ap and ap.type is TokenType.CONNECTIVE and ap.value == "and"):
                    break
                nx2 = stream.peek(1)
                # Sequencing wins if `and` is followed by a verb
                # (operation-sequencing §21 rule 3 still applies).
                if nx2 and nx2.type is TokenType.VERB:
                    break
                if nx2 and nx2.type is TokenType.QUOTED_STRING:
                    # v2c §87 — field names can't have spaces; quoted in
                    # this position is rejected with hyphenation guidance.
                    raise _ParseError(
                        f"Field names can't have spaces. Try a "
                        f"hyphenated name like '{_hyphenate(nx2.value)}' "
                        f"instead."
                    )
                if not (nx2 and nx2.type is TokenType.UNKNOWN):
                    break
                stream.consume()  # eat `and`
                fld = stream.consume()
                extras.append(fld.value)
            if extras:
                return ShowNode(
                    target=NameRef(name=peek.value),
                    extra_fields=extras,
                )
        return ShowNode(target=NameRef(name=peek.value))
    cat = reserved_category(peek.value)
    if cat:
        if peek.value == "each":
            # Issue #20: inside an `each` body, `show each` displays the
            # current iterator item — the natural pronoun form for the same
            # semantics as a bare `show` (target=None, v1c §49). Outside an
            # `each` body there is no iterator, so the pronoun is still an
            # error.
            if in_each:
                stream.consume()  # eat the `each` pronoun
                return ShowNode(target=None)
            raise _ParseError(
                "'each' is a verb in Liminate — it iterates a list, or "
                "acts as a self-reference pronoun inside a 'where' "
                "clause. It can't appear as a target on its own."
            )
        raise _ParseError(
            f"I expected a target after 'show', but '{peek.value}' is a "
            f"{cat} in Liminate. Targets must be names you've created "
            f"with 'remember' or 'gather'."
        )
    raise _ParseError(f"I didn't expect '{peek.value}' after 'show'.")


def _parse_count(stream: TokenStream) -> CountNode:
    _consume_optional_article(stream)
    target = _consume_target(stream, verb="count")
    return CountNode(target=target)


def _parse_sum(stream: TokenStream) -> SumNode:
    _consume_optional_article(stream)
    target = _consume_target(stream, verb="sum")
    return SumNode(target=target)


# ---------------------------------------------------------------------------
# add (Liminate `add` v1 §10)
# ---------------------------------------------------------------------------


def _parse_add(stream: TokenStream) -> AddNode:
    """`add [article]? <item-value> to [article]? <list-name>`."""
    _consume_optional_article(stream)
    if stream.at_end():
        raise _ParseError(
            "'add' needs an item and a target list — try: "
            "add <item> to <list-name>."
        )
    item = _parse_value(stream)
    to_tok = stream.consume()
    if not (to_tok and to_tok.type is TokenType.CONNECTIVE and to_tok.value == "to"):
        raise _ParseError(
            "'add' needs a target list — try: add <item> to <list-name>."
        )
    _consume_optional_article(stream)
    target = _consume_target(stream, verb="add")
    return AddNode(item=item, target=target)


# ---------------------------------------------------------------------------
# remove — retract an item from an existing list
# ---------------------------------------------------------------------------


def _parse_remove(stream: TokenStream) -> RemoveNode:
    """`remove [article]? <item-value> from [article]? <list-name>`."""
    _consume_optional_article(stream)
    if stream.at_end():
        raise _ParseError(
            "'remove' needs an item and a target list — try: "
            "remove <item> from <list-name>."
        )
    item = _parse_value(stream)
    from_tok = stream.consume()
    if not (
        from_tok and from_tok.type is TokenType.CONNECTIVE
        and from_tok.value == "from"
    ):
        raise _ParseError(
            "'remove' needs a source list — try: "
            "remove <item> from <list-name>."
        )
    _consume_optional_article(stream)
    target = _consume_target(stream, verb="remove")
    return RemoveNode(item=item, target=target)


# ---------------------------------------------------------------------------
# weakens (Metabolic Era batch 1)
# ---------------------------------------------------------------------------


def _parse_weakens(stream: TokenStream) -> WeakensNode:
    """`weakens [article]? <subject-name> over <number>`."""
    _consume_optional_article(stream)
    if stream.at_end():
        raise _ParseError(
            "'weakens' needs a target and a decay period — try: "
            "weakens <name> over <number>."
        )
    subject = _consume_target(stream, verb="weakens")

    over_tok = stream.consume()
    if not (
        over_tok
        and over_tok.type is TokenType.CONNECTIVE
        and over_tok.value == "over"
    ):
        raise _ParseError(
            "'weakens' needs a decay period — try: "
            "weakens <name> over <number>."
        )

    period_tok = stream.consume()
    if not (period_tok and period_tok.type is TokenType.NUMBER):
        raise _ParseError(
            "I expected a number after 'over' — the decay period. "
            "Try: weakens <name> over 30."
        )
    period = NumberLiteral(value=_parse_number(period_tok.value))
    return WeakensNode(subject=subject, period=period)


# ---------------------------------------------------------------------------
# require (Normative Era batch 2)
# ---------------------------------------------------------------------------


def _parse_require(stream: TokenStream) -> RequireNode | RequireEachNode:
    """`require <condition>` — enforcement verb.

    The condition uses the same parser path as `choose if` /
    `where` — `_parse_or_condition`, which supports compound
    `and`/`or`, `not`, `includes`, field access via `of`, and the
    full set of comparison operators. The clause-context stack is
    pushed so condition sub-parsers can see they're inside a
    `require` clause if they ever need to.

    v8a §49 — a second parse shape, `require each {name} in {list}
    {condition}`, is selected when the next token is the `each` verb.
    """
    if stream.at_end():
        raise _ParseError(
            "'require' needs a condition — try: "
            "require <field> is <operator> <value>."
        )

    # Second parse shape: `require each {name} in {list} {condition}`.
    peek = stream.peek()
    if peek and peek.type is TokenType.VERB and peek.value == "each":
        return _parse_require_each(stream)

    stream.push_clause("require")
    try:
        condition = _parse_or_condition(stream)
        exception = _try_consume_unless_exception(stream)
    finally:
        stream.pop_clause()
    return RequireNode(condition=condition, exception=exception)


def _parse_require_each(stream: TokenStream) -> RequireEachNode:
    """Parse `require each {name} in {list} {condition}` (v8a §49).

    `each` has been peeked but not consumed. Consume it, then the
    binding name (UNKNOWN, reserved-word-excluded), the positional `in`
    (UNKNOWN token, not a connective), the collection name, and finally
    the condition via the unified `_parse_or_condition` path.

    The `require-each` clause is pushed so `_parse_simple_condition`
    treats a field-elided condition (one that begins with `is` /
    `includes`) as referring to the current element via `EachPronoun`.
    """
    stream.consume()  # eat `each`

    # Binding name — an UNKNOWN token, never a reserved word.
    binding_name = _consume_name(stream, after="'require each'")

    # `in` — consumed positionally as an UNKNOWN token (it is not a
    # reserved connective; the same way `sort` consumes `in`).
    in_tok = stream.consume()
    if in_tok is None:
        raise _ParseError(
            "'require each' needs a list — try: "
            f"require each {binding_name} in <list-name> <condition>."
        )
    if not (in_tok.type is TokenType.UNKNOWN and in_tok.value == "in"):
        raise _ParseError(
            f"I expected 'in' after 'require each {binding_name}', "
            f"not '{in_tok.value}'. Try: "
            f"require each {binding_name} in <list-name> <condition>."
        )

    # Collection name.
    _consume_optional_article(stream)
    collection = _consume_target(stream, verb="require each")

    # Condition — same unified path as the simple `require`.
    if stream.at_end():
        raise _ParseError(
            f"'require each {binding_name} in {collection.name}' "
            f"needs a condition — try: require each {binding_name} "
            f"in {collection.name} is <operator> <value>."
        )
    stream.push_clause("require-each")
    try:
        condition = _parse_or_condition(stream)
    finally:
        stream.pop_clause()

    return RequireEachNode(
        binding_name=binding_name,
        collection=collection,
        condition=condition,
    )


# ---------------------------------------------------------------------------
# forbid (Deontic Era)
# ---------------------------------------------------------------------------


def _parse_forbid(stream: TokenStream) -> ForbidNode:
    """`forbid <condition>` — prohibition verb.

    Same condition grammar as `require`. The difference is purely
    in runtime behavior: `require` halts on false, `forbid` halts
    on true.
    """
    if stream.at_end():
        raise _ParseError(
            "'forbid' needs a condition — try: "
            "forbid <field> is <operator> <value>."
        )
    stream.push_clause("forbid")
    try:
        condition = _parse_or_condition(stream)
        exception = _try_consume_unless_exception(stream)
    finally:
        stream.pop_clause()
    return ForbidNode(condition=condition, exception=exception)


# ---------------------------------------------------------------------------
# permit (Deontic Era)
# ---------------------------------------------------------------------------


def _parse_permit(stream: TokenStream) -> PermitNode:
    """`permit <condition>` — explicit permission verb.

    Same condition grammar as `require`/`forbid`. The difference
    is purely in runtime behavior: `permit` emits on true, never
    halts.
    """
    if stream.at_end():
        raise _ParseError(
            "'permit' needs a condition — try: "
            "permit <field> is <operator> <value>."
        )
    stream.push_clause("permit")
    try:
        condition = _parse_or_condition(stream)
        exception = _try_consume_unless_exception(stream)
    finally:
        stream.pop_clause()
    return PermitNode(condition=condition, exception=exception)


# ---------------------------------------------------------------------------
# assign (Delegated Era batch 3)
# ---------------------------------------------------------------------------


def _parse_assign(stream: TokenStream) -> AssignNode:
    """`assign [article]? <item-name> to <recipient-value>`."""
    _consume_optional_article(stream)
    if stream.at_end():
        raise _ParseError(
            "'assign' needs an item and a recipient — try: "
            "assign <item> to <recipient>."
        )
    item = _consume_target(stream, verb="assign")

    to_tok = stream.consume()
    if not (
        to_tok and to_tok.type is TokenType.CONNECTIVE and to_tok.value == "to"
    ):
        raise _ParseError(
            "'assign' needs a recipient — try: "
            "assign <item> to <recipient>."
        )
    if stream.at_end():
        raise _ParseError(
            "I expected a recipient after 'to'. "
            "Try: assign <item> to <recipient>."
        )
    recipient = _parse_value(stream)
    return AssignNode(item=item, recipient=recipient)


# ---------------------------------------------------------------------------
# expect (Epistemic Era batch 3)
# ---------------------------------------------------------------------------


def _parse_expect(stream: TokenStream) -> ExpectNode:
    """`expect <condition>` — tracked anticipation verb.

    Same condition grammar as `require`. The difference is purely
    in runtime behavior: `require` halts on failure, `expect` reports
    and continues.
    """
    if stream.at_end():
        raise _ParseError(
            "'expect' needs a condition — try: "
            "expect <field> is <operator> <value>."
        )
    stream.push_clause("expect")
    try:
        condition = _parse_or_condition(stream)
        exception = _try_consume_unless_exception(stream)
    finally:
        stream.pop_clause()
    return ExpectNode(condition=condition, exception=exception)


# ---------------------------------------------------------------------------
# sort (Infrastructure Era batch 2)
# ---------------------------------------------------------------------------


def _parse_sort(stream: TokenStream) -> SortNode:
    """`sort [article]? <target> by <field> [in]? [reverse]?`.

    The optional `in` before `reverse` is NOT a reserved word — the
    parser consumes it as an UNKNOWN token only when `reverse` follows.
    This keeps the natural English phrasing (`sort by total in reverse`)
    while leaving `in` available as a user variable name elsewhere.
    """
    _consume_optional_article(stream)
    if stream.at_end():
        raise _ParseError(
            "'sort' needs a target list and a field — try: "
            "sort <list> by <field>."
        )
    target = _consume_target(stream, verb="sort")

    by_tok = stream.consume()
    if not (
        by_tok
        and by_tok.type is TokenType.CONNECTIVE
        and by_tok.value == "by"
    ):
        raise _ParseError(
            "'sort' needs a field to sort by — try: "
            "sort <list> by <field>."
        )

    field_tok = stream.consume()
    if field_tok is None:
        raise _ParseError("I expected a field name after 'by'.")
    if field_tok.type is TokenType.QUOTED_STRING:
        raise _ParseError(
            f"Field names can't have spaces. Try a hyphenated name "
            f"like '{_hyphenate(field_tok.value)}' instead."
        )
    if field_tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(field_tok.value)
        if cat:
            raise _ParseError(
                f"The word '{field_tok.value}' is reserved in Liminate "
                f"— it's used as a {cat}. Please use a field name "
                f"from your records."
            )
        raise _ParseError(
            f"I expected a field name after 'by', not '{field_tok.value}'."
        )
    field_name = field_tok.value

    descending = False
    peek = stream.peek()
    if (
        peek
        and peek.type is TokenType.UNKNOWN
        and peek.value == "in"
    ):
        # Only consume the `in` if `reverse` follows it. A lone trailing
        # `in` is left in the stream for the outer parser to surface.
        peek2 = stream.peek(1)
        if (
            peek2
            and peek2.type is TokenType.OPERATOR
            and peek2.value == "reverse"
        ):
            stream.consume()  # in
            stream.consume()  # reverse
            descending = True
    elif (
        peek
        and peek.type is TokenType.OPERATOR
        and peek.value == "reverse"
    ):
        stream.consume()  # reverse
        descending = True

    return SortNode(target=target, field=field_name, descending=descending)


# ---------------------------------------------------------------------------
# compare (V2 promotion)
# ---------------------------------------------------------------------------


def _parse_compare(stream: TokenStream) -> CompareNode:
    """`compare [article]? <left> to [article]? <right>`."""
    _consume_optional_article(stream)
    if stream.at_end():
        raise _ParseError(
            "'compare' needs two values — try: "
            "compare <name> to <name>."
        )
    left = _consume_target(stream, verb="compare")

    to_tok = stream.consume()
    if not (
        to_tok
        and to_tok.type is TokenType.CONNECTIVE
        and to_tok.value == "to"
    ):
        raise _ParseError(
            "'compare' needs a second value — try: "
            "compare <name> to <name>."
        )

    _consume_optional_article(stream)
    right = _consume_target(stream, verb="compare")

    return CompareNode(left=left, right=right)


# ---------------------------------------------------------------------------
# transform (final V2 promotion)
# ---------------------------------------------------------------------------


def _parse_transform(stream: TokenStream) -> TransformNode:
    """`transform <field> of <target> by <expression>`  (record-field mode)
    or `transform <target> by <expression>`             (scalar-list mode).

    Disambiguation: after consuming the first name, peek for `of`. If
    present, the first name is the field and the name after `of` is the
    target (record-field mode). If absent, the first name is the target
    (scalar-list mode).
    """
    _consume_optional_article(stream)
    if stream.at_end():
        raise _ParseError(
            "'transform' needs a target — try: "
            "transform <list> by <expression>, or "
            "transform <field> of <list> by <expression>."
        )

    first_tok = stream.consume()
    if first_tok is None:
        raise _ParseError("I expected a name after 'transform'.")
    if first_tok.type is TokenType.QUOTED_STRING:
        raise _ParseError(
            f"Names can't have spaces. Try a hyphenated name like "
            f"'{_hyphenate(first_tok.value)}' instead."
        )
    if first_tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(first_tok.value)
        if cat:
            raise _ParseError(
                f"The word '{first_tok.value}' is reserved in Liminate "
                f"— it's used as a {cat}. Please use a name you've "
                f"created."
            )
        raise _ParseError(
            f"I expected a name after 'transform', not '{first_tok.value}'."
        )

    peek = stream.peek()

    if peek and peek.type is TokenType.CONNECTIVE and peek.value == "of":
        # Record-field mode: first_tok is the field name.
        stream.consume()  # eat `of`
        _consume_optional_article(stream)
        target = _consume_target(stream, verb="transform")
        field_name = first_tok.value

        by_tok = stream.consume()
        if not (
            by_tok
            and by_tok.type is TokenType.CONNECTIVE
            and by_tok.value == "by"
        ):
            raise _ParseError(
                "'transform' needs an expression after 'by' — try: "
                f"transform {field_name} of {target.name} by <expression>."
            )
        if stream.at_end():
            raise _ParseError("I expected an expression after 'by'.")
        stream.push_clause("transform")
        try:
            expression = _parse_value(stream)
        finally:
            stream.pop_clause()
        return TransformNode(
            target=target, expression=expression, field=field_name,
        )

    if peek and peek.type is TokenType.CONNECTIVE and peek.value == "by":
        # Scalar-list mode: first_tok is the target.
        stream.consume()  # eat `by`
        target = NameRef(name=first_tok.value)
        if stream.at_end():
            raise _ParseError("I expected an expression after 'by'.")
        stream.push_clause("transform")
        try:
            expression = _parse_value(stream)
        finally:
            stream.pop_clause()
        return TransformNode(target=target, expression=expression, field=None)

    got = peek.value if peek else "end of line"
    raise _ParseError(
        f"I expected 'of' or 'by' after 'transform {first_tok.value}', "
        f"not '{got}'. Try: transform {first_tok.value} of <list> by "
        f"<expression>, or transform {first_tok.value} by <expression>."
    )


# ---------------------------------------------------------------------------
# gather
# ---------------------------------------------------------------------------


def _parse_gather(stream: TokenStream) -> GatherNode:
    _consume_optional_article(stream)
    name_tok = stream.consume()
    if name_tok is None:
        raise _ParseError("I expected a name after 'gather'.")
    if name_tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(name_tok.value)
        if cat:
            raise _ParseError(
                f"The word '{name_tok.value}' is reserved in Liminate — "
                f"it's used as a {cat}. Please choose a different name."
            )
        raise _ParseError(f"I expected a name after 'gather', not '{name_tok.value}'.")
    name = name_tok.value

    from_tok = stream.consume()
    if not (from_tok and from_tok.type is TokenType.CONNECTIVE and from_tok.value == "from"):
        raise _ParseError("I expected 'from' in 'gather'.")

    from_val_tok = stream.consume()
    if not from_val_tok or from_val_tok.type is not TokenType.NUMBER:
        raise _ParseError("I expected a number after 'from'.")
    from_val = _parse_number(from_val_tok.value)

    to_tok = stream.consume()
    if not (to_tok and to_tok.type is TokenType.CONNECTIVE and to_tok.value == "to"):
        raise _ParseError("I expected 'to' after the range start.")

    to_val_tok = stream.consume()
    if not to_val_tok or to_val_tok.type is not TokenType.NUMBER:
        raise _ParseError("I expected a number after 'to'.")
    to_val = _parse_number(to_val_tok.value)

    # D-6 — optional `by <number>` step value after `to <number>`. `by` is
    # already a connective (used by `sort`); its tail here is non-overlapping.
    step_val: int | float | None = None
    peek = stream.peek()
    if peek and peek.type is TokenType.CONNECTIVE and peek.value == "by":
        stream.consume()  # eat `by`
        step_tok = stream.consume()
        if not step_tok or step_tok.type is not TokenType.NUMBER:
            raise _ParseError("I expected a number after 'by' — the step value.")
        step_val = _parse_number(step_tok.value)
        if step_val <= 0:
            raise _ParseError(
                f"The step value must be positive — got {step_val}. "
                f"The direction is determined by the range (from/to), not the step."
            )

    return GatherNode(name=name, from_val=from_val, to_val=to_val, step_val=step_val)


# ---------------------------------------------------------------------------
# each
# ---------------------------------------------------------------------------


def _parse_each(stream: TokenStream, comp: set[str]) -> EachNode:
    _consume_optional_article(stream)
    coll_tok = stream.consume()
    if coll_tok is None:
        raise _ParseError("I expected a collection after 'each'.")
    if coll_tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(coll_tok.value)
        if cat:
            raise _ParseError(
                f"I expected a collection after 'each', but "
                f"'{coll_tok.value}' is a {cat} in Liminate. Collections "
                f"must be names you've created with 'remember' or 'gather'."
            )
        raise _ParseError(f"I expected a collection after 'each'.")
    collection = NameRef(name=coll_tok.value)

    if stream.at_end():
        raise _ParseError("I expected an action for 'each'.")

    stream.push_clause("each")
    try:
        # v2a §69: the show parser keys multi-field detection off this
        # clause-context flag — see _parse_verb_statement / _parse_show.
        action = _parse_one_operation(stream, comp)
    finally:
        stream.pop_clause()
    return EachNode(collection=collection, action=action)


# ---------------------------------------------------------------------------
# choose (v2d §99–§102)
# ---------------------------------------------------------------------------


def _parse_choose(stream: TokenStream, comp: set[str]) -> ChooseNode:
    """Parse `choose if <cond>: <action> [otherwise [if <cond>:] <action>]*`.

    The colon is the context switch between condition mode and action
    mode (§101). Conditions reuse the where-clause condition path
    (`_parse_or_condition`) so `and`/`or` compose as in `where` — they
    terminate at `:`. Actions reuse `_parse_operation_sequence` so `and
    <verb>` sequences operations within a branch — it terminates at
    `otherwise` and at end of input.
    """
    if_tok = stream.consume()
    if not (if_tok and if_tok.type is TokenType.CONNECTIVE and if_tok.value == "if"):
        raise _ParseError(
            "I expected 'if' after 'choose'. "
            "Try: choose if <condition>: <action>."
        )
    branches: list[ChooseBranch] = [
        _parse_choose_branch(stream, comp, leader="'choose if'")
    ]
    while True:
        peek = stream.peek()
        if not (peek and peek.type is TokenType.CONNECTIVE and peek.value == "otherwise"):
            break
        stream.consume()  # eat `otherwise`
        peek2 = stream.peek()
        if peek2 and peek2.type is TokenType.CONNECTIVE and peek2.value == "if":
            stream.consume()  # eat the chained `if`
            branches.append(
                _parse_choose_branch(stream, comp, leader="'otherwise if'")
            )
        else:
            # Terminal `otherwise <action>` — no condition, no colon (§99).
            action = _parse_operation_sequence(stream, comp)
            branches.append(ChooseBranch(condition=None, action=action))
            # No further branches are syntactically allowed after the
            # terminal otherwise — additional tokens are left for the
            # outer parser, which surfaces them as unexpected.
            break
    return ChooseNode(branches=branches)


def _parse_choose_branch(
    stream: TokenStream, comp: set[str], *, leader: str,
) -> ChooseBranch:
    """Parse `<condition>: <action>` for a single `choose` branch. The
    `leader` argument feeds the error message so the user sees whether
    they were inside the initial `choose if` or a chained `otherwise if`."""
    stream.push_clause("choose_cond")
    try:
        condition = _parse_or_condition(stream)
    finally:
        stream.pop_clause()
    colon = stream.consume()
    if not (colon and colon.type is TokenType.DELIMITER and colon.value == ":"):
        got = colon.value if colon else "end of line"
        raise _ParseError(
            f"I expected ':' after the {leader} condition, not '{got}'."
        )
    action = _parse_operation_sequence(stream, comp)
    return ChooseBranch(condition=condition, action=action)


# ---------------------------------------------------------------------------
# filter + where conditions
# ---------------------------------------------------------------------------


def _parse_filter(stream: TokenStream) -> FilterNode:
    target, condition = _parse_filter_shape(stream, verb="filter")
    return FilterNode(target=target, condition=condition)


def _parse_keep(stream: TokenStream) -> KeepNode:
    """v2a §67. Shares the target + where + condition shape with filter."""
    target, condition = _parse_filter_shape(stream, verb="keep")
    return KeepNode(target=target, condition=condition)


def _parse_filter_shape(
    stream: TokenStream, *, verb: str,
) -> tuple[NameRef, ASTNode]:
    """Shared parser for the filter/keep shape: optional article + target
    + 'where' + condition. v2a §67 keeps the two verbs structurally
    identical at parse time; the difference lives in the interpreter."""
    _consume_optional_article(stream)
    target = _consume_target(stream, verb=verb)

    where_tok = stream.consume()
    if not (where_tok and where_tok.type is TokenType.CONNECTIVE and where_tok.value == "where"):
        raise _ParseError("I expected 'where' to introduce the condition.")

    stream.push_clause("where")
    try:
        condition = _parse_or_condition(stream)
    finally:
        stream.pop_clause()
    return target, condition


def _parse_or_condition(stream: TokenStream) -> ASTNode:
    left = _parse_and_condition(stream)
    while True:
        peek = stream.peek()
        if not (peek and peek.type is TokenType.CONNECTIVE and peek.value == "or"):
            break
        nxt = stream.peek(1)
        if nxt and nxt.type is TokenType.VERB:
            break  # operation sequencing
        stream.consume()
        right = _parse_and_condition(stream)
        left = CompoundConditionNode(left=left, right=right, connector="or")
    return left


def _parse_and_condition(stream: TokenStream) -> ASTNode:
    left = _parse_simple_condition(stream)
    while True:
        peek = stream.peek()
        if not (peek and peek.type is TokenType.CONNECTIVE and peek.value == "and"):
            break
        nxt = stream.peek(1)
        if nxt and nxt.type is TokenType.VERB:
            break  # operation sequencing — exit the where clause
        stream.consume()
        right = _parse_simple_condition(stream)
        left = CompoundConditionNode(left=left, right=right, connector="and")
    return left


def _parse_simple_condition(stream: TokenStream) -> ConditionNode:
    # Field reference or `each` pronoun (v1b §37).
    head = stream.peek()
    if head is None:
        raise _ParseError("I expected a field after 'where'.")
    # v8a §49 — inside `require each`, a condition may elide its field:
    # `is above 70` / `includes "x"` with no LHS binds to the current
    # element via an implicit `each` pronoun. Detect the elided form by a
    # leading comparison/membership token and inject EachPronoun without
    # consuming it, so the operator-parsing below proceeds normally.
    if stream.in_clause("require-each") and (
        (head.type is TokenType.OPERATOR and head.value in ("is", "not"))
        or (head.type is TokenType.CONNECTIVE and head.value == "includes")
    ):
        field_node: ASTNode = EachPronoun()
        return _finish_simple_condition(stream, field_node)
    # v25 VW-Q2 — `highest`/`lowest` as a condition's left-hand side, e.g.
    # `require highest total of line-items is below single-item-cap`.
    if head.type is TokenType.OPERATOR and head.value in ("highest", "lowest"):
        field_node = _parse_extrema(stream)
        return _finish_simple_condition(stream, field_node)
    head = stream.consume()
    if head.type is TokenType.VERB and head.value == "each":
        field_node: ASTNode = EachPronoun()
    elif head.type is TokenType.UNKNOWN:
        # v2b §77 / v2d §100: support `<field> of <record>` on the left
        # side of a comparison. `where`/`keep` conditions normally read
        # the field off the iterator item, but `choose` has no iterator —
        # users must point to a record explicitly with `of`. Allowing it
        # uniformly here is a strict additive change (previously a
        # parse error), and the analyzer applies the same field-access
        # checks regardless of clause context.
        after = stream.peek()
        if after and after.type is TokenType.CONNECTIVE and after.value == "of":
            stream.consume()  # eat `of`
            rec_tok = stream.consume()
            if rec_tok is None:
                raise _ParseError("I expected a record name after 'of'.")
            if rec_tok.type is not TokenType.UNKNOWN:
                rcat = reserved_category(rec_tok.value)
                if rcat:
                    raise _ParseError(
                        f"The word '{rec_tok.value}' is reserved in "
                        f"Liminate — it's used as a {rcat} and can't be "
                        f"used as a record name."
                    )
                raise _ParseError(
                    f"I expected a record name after 'of', not "
                    f"'{rec_tok.value}'."
                )
            chain = stream.peek()
            if chain and chain.type is TokenType.CONNECTIVE and chain.value == "of":
                raise _ParseError(
                    "Field access uses one record at a time: "
                    "<field> of <record>. Chained forms (a of b of c) "
                    "need nested records, which v2b doesn't yet have."
                )
            field_node = FieldAccessNode(field=head.value, record_name=rec_tok.value)
        else:
            field_node = NameRef(name=head.value)
    elif head.type is TokenType.QUOTED_STRING:
        # v2c §87 — field names can't have spaces.
        raise _ParseError(
            f"Field names can't have spaces. Try a hyphenated name like "
            f"'{_hyphenate(head.value)}' instead."
        )
    else:
        cat = reserved_category(head.value)
        if cat:
            raise _ParseError(
                f"The word '{head.value}' is reserved in Liminate — "
                f"it's used as a {cat} and can't be used as a field name."
            )
        raise _ParseError(f"I didn't expect '{head.value}' as a field name.")

    return _finish_simple_condition(stream, field_node)


def _finish_simple_condition(stream: TokenStream, field_node: ASTNode) -> ConditionNode:
    """Parse the operator + value tail of a simple condition, given an
    already-resolved field node. Shared between the explicit-field path
    and the `require each` field-elided path (v8a §49)."""
    # `includes` is a list-membership connective; it replaces the entire
    # `is <op>` pattern: `<list> includes <value>` or
    # `<list> not includes <value>`.
    nxt = stream.peek()
    if nxt and nxt.type is TokenType.CONNECTIVE and nxt.value == "includes":
        stream.consume()
        value = _parse_value(stream)
        return ConditionNode(field=field_node, op="includes", value=value)
    if nxt and nxt.type is TokenType.OPERATOR and nxt.value == "not":
        after = stream.peek(1)
        if (
            after is not None
            and after.type is TokenType.CONNECTIVE
            and after.value == "includes"
        ):
            stream.consume()  # not
            stream.consume()  # includes
            value = _parse_value(stream)
            return ConditionNode(field=field_node, op="not_includes", value=value)

    is_tok = stream.consume()
    if not (is_tok and is_tok.type is TokenType.OPERATOR and is_tok.value == "is"):
        raise _ParseError("I expected 'is' in this condition.")

    # `is` is a comparison introducer if next token is a known operator
    # (above/below/equal_to/not); otherwise `is` itself is equality (§21).
    nxt = stream.peek()
    if nxt is None:
        raise _ParseError("I expected a value or comparison after 'is'.")

    # `is within <amount> of <target>` — numeric tolerance (issue #19):
    # true when |field - target| <= amount. `within` is a connective, so
    # it is dispatched here rather than in the OPERATOR branch below.
    if nxt.type is TokenType.CONNECTIVE and nxt.value == "within":
        stream.consume()  # eat `within`
        tolerance = _parse_within_tolerance(stream)
        of_tok = stream.consume()
        if not (of_tok and of_tok.type is TokenType.CONNECTIVE and of_tok.value == "of"):
            got = of_tok.value if of_tok else "end of line"
            raise _ParseError(
                f"'within' needs a target — try: "
                f"<field> is within <amount> of <target>. Got: {got}."
            )
        target = _parse_value(stream)
        return ConditionNode(
            field=field_node, op="within", value=tolerance, value2=target,
        )

    if nxt.type is TokenType.OPERATOR:
        if nxt.value == "not":
            stream.consume()
            inner = stream.consume()
            if not (
                inner
                and inner.type is TokenType.OPERATOR
                and inner.value in _COMPARISON_OPERATORS
            ):
                raise _ParseError(
                    "After 'not' I expected 'above', 'below', or 'equal to'."
                )
            op = f"not_{inner.value}"
            value = _parse_value(stream)
            return ConditionNode(field=field_node, op=op, value=value)
        if nxt.value in _COMPARISON_OPERATORS:
            stream.consume()
            value = _parse_value(stream)
            return ConditionNode(field=field_node, op=nxt.value, value=value)
        raise _ParseError(f"I didn't expect '{nxt.value}' after 'is'.")

    # `is` as equality operator: consume a value.
    value = _parse_value(stream)
    return ConditionNode(field=field_node, op="is", value=value)


def _parse_within_tolerance(stream: TokenStream) -> ASTNode:
    """Parse the tolerance operand of `is within <amount> of <target>`
    (issue #19) as a single bare atom — a number literal or a name.

    This deliberately does NOT go through `_parse_value`: that would let
    `_maybe_field_access` swallow the structural `of` (reading the
    tolerance and target as a single `<name> of <record>` field access),
    so `within tol of target` would lose its `of`. A name resolves to its
    numeric value at evaluation time (a `BareWord`, like any other
    right-hand condition operand)."""
    tok = stream.consume()
    if tok is None:
        raise _ParseError(
            "'within' needs an amount — try: "
            "<field> is within <amount> of <target>."
        )
    if tok.type is TokenType.NUMBER:
        return NumberLiteral(value=_parse_number(tok.value))
    if tok.type is TokenType.UNKNOWN:
        return BareWord(word=tok.value)
    cat = reserved_category(tok.value)
    if cat:
        raise _ParseError(
            f"'within' needs a numeric amount, but '{tok.value}' is a "
            f"{cat} in Liminate."
        )
    raise _ParseError(
        f"'within' needs a numeric amount, not '{tok.value}'."
    )


# ---------------------------------------------------------------------------
# Value parsing (literals + name references)
# ---------------------------------------------------------------------------


_ADDITIVE_OPS = frozenset({"plus", "minus"})
_MULTIPLICATIVE_OPS = frozenset({"multiplied_by", "divided_by"})


def _parse_value(stream: TokenStream) -> ASTNode:
    """Parse a value expression, which may include arithmetic.

    Precedence (Infrastructure Era — PEMDAS):
      Tier 1 (lowest):  plus, minus                — left-associative
      Tier 2 (highest): multiplied_by, divided_by  — left-associative
      Atoms: NUMBER, UNKNOWN (with optional `of`), QUOTED_STRING

    Every call site that previously consumed a single value via
    `_parse_value` now transparently supports arithmetic expressions in
    that position.
    """
    return _parse_additive(stream)


def _parse_additive(stream: TokenStream) -> ASTNode:
    left = _parse_multiplicative(stream)
    while True:
        peek = stream.peek()
        if not (
            peek
            and peek.type is TokenType.OPERATOR
            and peek.value in _ADDITIVE_OPS
        ):
            break
        stream.consume()
        right = _parse_multiplicative(stream)
        left = ArithmeticNode(left=left, right=right, op=peek.value)
    return left


def _parse_multiplicative(stream: TokenStream) -> ASTNode:
    left = _parse_atom(stream)
    while True:
        peek = stream.peek()
        if not (
            peek
            and peek.type is TokenType.OPERATOR
            and peek.value in _MULTIPLICATIVE_OPS
        ):
            break
        stream.consume()
        right = _parse_atom(stream)
        left = ArithmeticNode(left=left, right=right, op=peek.value)
    return left


def _parse_extrema(stream: TokenStream) -> ExtremaNode:
    """v25 VW-Q1/Q2 — `highest`/`lowest` list-extrema selector.

    Form A (flat lists):   highest of <list>
    Form B (record lists): highest <field> of <list>

    The OPERATOR token (`highest`/`lowest`) has been peeked, not
    consumed, by the caller.
    """
    word_tok = stream.consume()
    word = word_tok.value
    nxt = stream.peek()
    if nxt and nxt.type is TokenType.CONNECTIVE and nxt.value == "of":
        stream.consume()  # eat `of`
        _consume_optional_article(stream)
        target = _consume_target(stream, verb=word)
        field_name = None
    elif (
        nxt
        and nxt.type is TokenType.UNKNOWN
        and stream.peek(1) is not None
        and stream.peek(1).type is TokenType.CONNECTIVE
        and stream.peek(1).value == "of"
    ):
        field_tok = stream.consume()
        stream.consume()  # eat `of`
        _consume_optional_article(stream)
        target = _consume_target(stream, verb=word)
        field_name = field_tok.value
    else:
        raise _ParseError(
            f"'{word}' needs a list — try: {word} of <list>, or "
            f"{word} <field> of <list>."
        )
    # v2b §77 sub-decision I precedent: chained `of` is a parse error
    # (no nested records).
    chain = stream.peek()
    if chain and chain.type is TokenType.CONNECTIVE and chain.value == "of":
        raise _ParseError(
            "Field access uses one record at a time: "
            "<field> of <record>. Chained forms (a of b of c) "
            "need nested records, which v2b doesn't yet have."
        )
    return ExtremaNode(word=word, target=target, field=field_name)


def _parse_atom(stream: TokenStream) -> ASTNode:
    """Consume a single value token (NUMBER, UNKNOWN, or QUOTED_STRING),
    optionally extended by `of <record>` for field access (v2b §77).

    Vocabulary words in value position are rejected per v1c §46 (extended
    by v2c §89 — the error message now suggests quoting as the fix).
    """
    peek = stream.peek()
    if peek and peek.type is TokenType.OPERATOR and peek.value in ("highest", "lowest"):
        return _parse_extrema(stream)
    tok = stream.consume()
    if tok is None:
        raise _ParseError("I expected a value here.")
    if tok.type is TokenType.NUMBER:
        return NumberLiteral(value=_parse_number(tok.value))
    if tok.type is TokenType.UNKNOWN:
        # v2b §77: `<field> of <record>` field-access value expression.
        # v25: this branch also covers tombstoned words (e.g. `combine`)
        # in value position — they lex as UNKNOWN like any other bare
        # word and fall through to BareWord/QuotedString-equivalent data
        # semantics rather than an error. Deliberate: keeps the freeing
        # path open (VW-Q6) and matches quoted-reserved-word handling.
        return _maybe_field_access(stream, tok.value)
    if tok.type is TokenType.QUOTED_STRING:
        # v2c §87 — quoted multi-word/reserved-word literal. §89: the
        # vocabulary check is bypassed for quoted tokens. Reject a
        # following `of` (field names can't be quoted, §87).
        after = stream.peek()
        if after and after.type is TokenType.CONNECTIVE and after.value == "of":
            raise _ParseError(
                f"Field names can't have spaces. Try '{_hyphenate(tok.value)}' "
                f"instead of \"{tok.value}\"."
            )
        return QuotedString(content=tok.value)
    # Final V2 promotion: allow `each` as a self-reference pronoun in
    # value position inside a `transform` clause (scalar-list mode), the
    # same way it acts as a pronoun inside a `where` condition (v1b §37).
    # It resolves to the current element during per-element evaluation.
    if tok.type is TokenType.VERB and tok.value == "each":
        # Phase 3 Spec 2: a pack verb with a "value"-typed slot can also
        # take `each` inside an enclosing `each` block (iterable pack verbs).
        if stream.in_clause("transform") or stream.in_clause("each"):
            return EachPronoun()
        raise _ParseError(
            "'each' is a verb in Liminate — it iterates a list, or "
            "acts as a self-reference pronoun inside a 'where' "
            "clause. It can't appear as a value on its own."
        )
    cat = reserved_category(tok.value)
    if cat:
        raise _ParseError(
            f"The word '{tok.value}' is a {cat} in Liminate and can't be "
            f"used as a value. Try a different word, or wrap it in quotes: "
            f'"{tok.value}".'
        )
    raise _ParseError(f"I didn't expect '{tok.value}' as a value.")


def _hyphenate(quoted_content: str) -> str:
    """v2c §87 — turn the content of a quoted string into a hyphenated
    name suggestion: spaces become hyphens. `"my big list"` → `my-big-list`.
    Used by all "names can't have spaces" / "field names can't have
    spaces" error messages."""
    return quoted_content.replace(" ", "-")


def _maybe_field_access(stream: TokenStream, first_unknown: str) -> ASTNode:
    """v2b §77 — if the next token is the connective `of`, consume the
    field-access tail and return FieldAccessNode. Otherwise return a
    BareWord with the already-consumed UNKNOWN. Single-level only:
    a second `of` after the record name is a parse error.
    """
    after = stream.peek()
    if not (after and after.type is TokenType.CONNECTIVE and after.value == "of"):
        return BareWord(word=first_unknown)
    stream.consume()  # eat `of`
    rec_tok = stream.consume()
    if rec_tok is None:
        raise _ParseError("I expected a record name after 'of'.")
    if rec_tok.type is not TokenType.UNKNOWN:
        rcat = reserved_category(rec_tok.value)
        if rcat:
            raise _ParseError(
                f"The word '{rec_tok.value}' is reserved in "
                f"Liminate — it's used as a {rcat} and can't be "
                f"used as a record name."
            )
        raise _ParseError(
            f"I expected a record name after 'of', not '{rec_tok.value}'."
        )
    chain = stream.peek()
    if chain and chain.type is TokenType.CONNECTIVE and chain.value == "of":
        raise _ParseError(
            "Field access uses one record at a time: <field> of <record>. "
            "Chained forms (a of b of c) need nested records, which v2b "
            "doesn't yet have."
        )
    return FieldAccessNode(field=first_unknown, record_name=rec_tok.value)


def _parse_number(s: str) -> int | float:
    return float(s) if "." in s else int(s)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _consume_optional_article(stream: TokenStream) -> None:
    t = stream.peek()
    if t and t.type is TokenType.ARTICLE:
        stream.consume()


def _consume_target(stream: TokenStream, *, verb: str) -> NameRef:
    tok = stream.consume()
    # D10 (v2.1-patch): per-record decisions don't exist as a v2b feature.
    # When `keep` or `filter` appears inside an `each` body, the user has
    # asked for per-record-decision logic that v2b deliberately doesn't
    # provide (the model is list-level filtering). Surface the list-level
    # alternative rather than the generic "expected a target" error.
    if (
        verb in ("keep", "filter")
        and stream.in_clause("each")
        and (tok is None or tok.type is not TokenType.UNKNOWN)
    ):
        raise _ParseError(
            f"'{verb}' is a list operation — it can't appear inside "
            f"'each'. To {verb} only some items, use "
            f"'{verb} <list> where <condition>' directly."
        )
    if tok is None:
        raise _ParseError(f"I expected a target after '{verb}'.")
    if tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(tok.value)
        if cat:
            # 'each' is both a verb and the in-`where` pronoun (v1b §37) —
            # surface that distinction when it appears as a target.
            if tok.value == "each":
                raise _ParseError(
                    "'each' is a verb in Liminate — it iterates a list, or "
                    "acts as a self-reference pronoun inside a 'where' "
                    "clause. It can't appear as a target on its own."
                )
            raise _ParseError(
                f"I expected a target after '{verb}', but '{tok.value}' "
                f"is a {cat} in Liminate. Targets must be names you've "
                f"created with 'remember' or 'gather'."
            )
        raise _ParseError(f"I expected a target after '{verb}', not '{tok.value}'.")
    return NameRef(name=tok.value)


def _consume_parameter_arg(stream: TokenStream, *, comp_name: str) -> str | ASTNode:
    """Phase 2 D-1 — consume the argument token that follows `<comp> from`
    at a call site. Atoms only: a bare name (UNKNOWN → symbol-table name,
    returned as a string for the existing lookup path), a numeric literal
    (NUMBER → `NumberLiteral`), or a quoted string (QUOTED_STRING →
    `QuotedString`). Reserved words and end-of-line are rejected. No full
    value expressions — no arithmetic, no `of` field access.

    Returning `str` preserves the v2d §96 names-only path verbatim; the
    AST-node returns are the new literal path. Name lookup still happens at
    run time, consistent with v1's name-resolution timing (inception §23).
    """
    tok = stream.consume()
    if tok is None:
        raise _ParseError(
            f"I expected a name after '{comp_name} from' — "
            f"compositions take a single name as input."
        )
    if tok.type is TokenType.NUMBER:
        return NumberLiteral(value=_parse_number(tok.value))
    if tok.type is TokenType.QUOTED_STRING:
        return QuotedString(content=tok.value)
    if tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(tok.value)
        if cat:
            raise _ParseError(
                f"The word '{tok.value}' is reserved in Liminate — "
                f"it's used as a {cat}. Please use a name you've created."
            )
        raise _ParseError(
            f"I expected a name after '{comp_name} from', not '{tok.value}'."
        )
    return tok.value


def _consume_name(stream: TokenStream, *, after: str) -> str:
    tok = stream.consume()
    if tok is None:
        raise _ParseError(f"I expected a name after {after}.")
    if tok.type is TokenType.QUOTED_STRING:
        # v2c §87 — names can't have spaces. Distinguish composition
        # names (after `how to`) from value names (after `called`) so
        # the error message matches what the user wrote.
        suggestion = _hyphenate(tok.value)
        if "how to" in after:
            raise _ParseError(
                f"Composition names can't have spaces. Try a hyphenated "
                f"name like '{suggestion}' instead."
            )
        raise _ParseError(
            f"Names can't have spaces. Try a hyphenated name like "
            f"'{suggestion}' instead."
        )
    if tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(tok.value)
        if cat:
            raise _ParseError(
                f"The word '{tok.value}' is reserved in Liminate — "
                f"it's used as a {cat}. Please choose a different name."
            )
        raise _ParseError(f"I expected a name after {after}, not '{tok.value}'.")
    # v4a §137: pack-reserved words (active pack nouns) remain UNKNOWN
    # tokens because they are not base vocabulary, but they must still be
    # rejected in name positions while their pack is loaded.
    cat = reserved_category(tok.value)
    if cat:
        raise _ParseError(
            f"The word '{tok.value}' is reserved in Liminate — "
            f"it's used as a {cat}. Please choose a different name."
        )
    return tok.value


def _contains_mixed_precedence(node: ASTNode) -> bool:
    """Return True if any condition tree in `node` mixes `and` with `or`."""
    if isinstance(node, (FilterNode, KeepNode)):
        return _condition_is_mixed(node.condition)
    if isinstance(node, RequireNode):
        # Normative Era batch 2: `require` conditions follow the same
        # mixed-precedence rule as `where` / `choose if` clauses (v1a §30).
        # v28: the `unless` exception condition follows the same rule.
        if _condition_is_mixed(node.condition):
            return True
        return node.exception is not None and _condition_is_mixed(node.exception)
    if isinstance(node, RequireEachNode):
        # v8a §49: `require each` conditions follow the same
        # mixed-precedence rule as the simple `require`.
        return _condition_is_mixed(node.condition)
    if isinstance(node, ForbidNode):
        # Deontic Era: `forbid` conditions follow the same
        # mixed-precedence rule as `require` / `where`.
        # v28: the `unless` exception condition follows the same rule.
        if _condition_is_mixed(node.condition):
            return True
        return node.exception is not None and _condition_is_mixed(node.exception)
    if isinstance(node, PermitNode):
        # Deontic Era: `permit` conditions follow the same
        # mixed-precedence rule as `require` / `forbid` / `where`.
        # v28: the `unless` exception condition follows the same rule.
        if _condition_is_mixed(node.condition):
            return True
        return node.exception is not None and _condition_is_mixed(node.exception)
    if isinstance(node, ExpectNode):
        # Epistemic Era batch 3: `expect` conditions follow the same
        # mixed-precedence rule as `require` / `where`.
        # v28: the `unless` exception condition follows the same rule.
        if _condition_is_mixed(node.condition):
            return True
        return node.exception is not None and _condition_is_mixed(node.exception)
    if isinstance(node, SequenceNode):
        return any(_contains_mixed_precedence(op) for op in node.operations)
    if isinstance(node, EachNode):
        return _contains_mixed_precedence(node.action)
    if isinstance(node, RememberCompositionNode):
        return _contains_mixed_precedence(node.body)
    if isinstance(node, RememberValueNode) and isinstance(node.value, ASTNode):
        return _contains_mixed_precedence(node.value)
    if isinstance(node, ChooseNode):
        # v2d §100 / §101: amber applies to `choose` conditions on the
        # same grounds as `where` clauses (v1a §30). Each branch's
        # condition tree (where present) is independently checked; the
        # branch action may itself be a SequenceNode containing a
        # filter/keep, so recurse into it too.
        for br in node.branches:
            if br.condition is not None and _condition_is_mixed(br.condition):
                return True
            if _contains_mixed_precedence(br.action):
                return True
    if isinstance(node, WhenNode):
        # v3a §123: mixed and/or in `when` or `unless` conditions triggers
        # amber at registration time. Action statements may themselves
        # contain where/choose conditions, so recurse into them too — an
        # unresolved amber anywhere in a handler still blocks Phase 2 per
        # v3a §107.
        if _condition_is_mixed(node.condition):
            return True
        if node.unless is not None and _condition_is_mixed(node.unless):
            return True
        if _contains_mixed_precedence(node.action):
            return True
    return False


def _condition_is_mixed(node: ASTNode) -> bool:
    seen = {"and": False, "or": False}

    def walk(n: ASTNode) -> None:
        if isinstance(n, CompoundConditionNode):
            seen[n.connector] = True
            walk(n.left)
            walk(n.right)

    walk(node)
    return seen["and"] and seen["or"]

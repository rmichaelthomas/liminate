"""Canonical prose renderer for Inscript v1.

Sources:
- v1a §33 (canonical prose rendering is a parser output requirement —
  used for intent verification, obfuscation prevention, and round-trip
  fidelity).
- v1b §42 (display formats — separate concern, lives in interpreter).

The canonical rendering is the inverse of parsing: it walks the AST and
emits a paren-free English sentence in canonical slot order. Round-trip
property: `parse(tokenize(render(ast)))` must equal `ast`.

A second entry point — `render_with_explicit_precedence` — emits the
same AST with parenthesized compound conditions, used for the AMBER
precedence message (v1a §30, v1c §50 outcome 2). This rendering is not
required to round-trip through the parser.
"""

from __future__ import annotations

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
    FieldAccessNode,
    FilterNode,
    GatherNode,
    KeepNode,
    NameRef,
    NumberLiteral,
    QuotedString,
    RememberCompositionNode,
    RememberListNode,
    RememberRecordNode,
    RememberValueNode,
    SequenceNode,
    ShowNode,
)
from .vocabulary import ALL_RESERVED


def render(node: ASTNode) -> str:
    """Canonical (paren-free) prose rendering of an AST node."""
    if isinstance(node, NumberLiteral):
        return _fmt_number(node.value)
    if isinstance(node, BareWord):
        # v2c §90: conditional quoting — quote multi-word or reserved-word
        # values to preserve round-trip integrity. Single-word non-reserved
        # values remain bare (v1 behavior unchanged).
        return _emit_string(node.word)
    if isinstance(node, QuotedString):
        # v2c §90: same conditional-quoting rule applies regardless of
        # whether the source used quotes — `"active"` and `active` both
        # render bare; `"in progress"` keeps its quotes.
        return _emit_string(node.content)
    if isinstance(node, NameRef):
        return node.name
    if isinstance(node, EachPronoun):
        return "each"
    if isinstance(node, FieldAccessNode):
        # v2b §77: <field> of <record> renders verbatim.
        return f"{node.field} of {node.record_name}"

    if isinstance(node, RememberValueNode):
        # v2a §71 / D6: preserve the user's descriptor verbatim. When the
        # user wrote no descriptor, fall back to the inferred type label
        # ("value" for a scalar; "list"/"record" for the other node types).
        desc = node.descriptor or "value"
        art = _article_for(desc)
        # Literals/strings go through `with`; name references and verb-phrase
        # results go through `from` (v1b §43). Vocabulary words cannot
        # appear after `with` (v1c §46), so verb-phrase values must use
        # `from` for the canonical form to be re-parseable.
        if isinstance(node.value, (NumberLiteral, BareWord)):
            return f"remember {art} {desc} called {node.name} with {render(node.value)}"
        return f"remember {art} {desc} called {node.name} from {render(node.value)}"
    if isinstance(node, RememberListNode):
        items = " and ".join(render(i) for i in node.items)
        desc = node.descriptor or "list"
        art = _article_for(desc)
        return f"remember {art} {desc} called {node.name} with {items}"
    if isinstance(node, RememberRecordNode):
        fields = " and ".join(f"{n} as {render(v)}" for n, v in node.fields)
        desc = node.descriptor or "record"
        art = _article_for(desc)
        return f"remember {art} {desc} called {node.name} with {fields}"
    if isinstance(node, RememberCompositionNode):
        return f"remember how to {node.name}: {render(node.body)}"

    if isinstance(node, ShowNode):
        if node.target is None:
            return "show"
        # v2a §68 (D4): `show <field> of <record>` renders back exactly
        # as the user wrote it.
        if node.record_name is not None:
            return f"show {render(node.target)} of {node.record_name}"
        # v2a §69 (D1): multi-field display inside `each ... show`.
        if node.extra_fields:
            fields = " and ".join([render(node.target), *node.extra_fields])
            return f"show {fields}"
        return f"show {render(node.target)}"
    if isinstance(node, FilterNode):
        return f"filter the {render(node.target)} where {render(node.condition)}"
    if isinstance(node, KeepNode):
        # v2a §67: `keep` shares filter's canonical shape.
        return f"keep the {render(node.target)} where {render(node.condition)}"
    if isinstance(node, CountNode):
        return f"count the {render(node.target)}"
    if isinstance(node, GatherNode):
        return (
            f"gather the {node.name} "
            f"from {_fmt_number(node.from_val)} to {_fmt_number(node.to_val)}"
        )
    if isinstance(node, CombineNode):
        return f"combine the {render(node.target)}"
    if isinstance(node, EachNode):
        return f"each the {render(node.collection)} {render(node.action)}"

    if isinstance(node, CompositionCallNode):
        return node.name
    if isinstance(node, SequenceNode):
        return " and ".join(render(op) for op in node.operations)

    if isinstance(node, ConditionNode):
        return _render_condition(node)
    if isinstance(node, CompoundConditionNode):
        return f"{render(node.left)} {node.connector} {render(node.right)}"

    raise TypeError(f"render() has no rule for {type(node).__name__}")


def render_with_explicit_precedence(node: ASTNode) -> str:
    """Render with parentheses around mixed-precedence compound conditions.

    Used in the AMBER_PRECEDENCE message (v1a §30) to show how the parser
    grouped a mixed `and`/`or` clause.
    """
    if isinstance(node, CompoundConditionNode):
        l = render_with_explicit_precedence(node.left)
        r = render_with_explicit_precedence(node.right)
        if (
            isinstance(node.left, CompoundConditionNode)
            and node.left.connector != node.connector
        ):
            l = f"({l})"
        if (
            isinstance(node.right, CompoundConditionNode)
            and node.right.connector != node.connector
        ):
            r = f"({r})"
        return f"{l} {node.connector} {r}"
    if isinstance(node, FilterNode):
        return (
            f"filter the {render(node.target)} where "
            f"{render_with_explicit_precedence(node.condition)}"
        )
    if isinstance(node, KeepNode):
        return (
            f"keep the {render(node.target)} where "
            f"{render_with_explicit_precedence(node.condition)}"
        )
    if isinstance(node, EachNode):
        return f"each the {render(node.collection)} {render_with_explicit_precedence(node.action)}"
    if isinstance(node, SequenceNode):
        return " and ".join(render_with_explicit_precedence(op) for op in node.operations)
    if isinstance(node, RememberCompositionNode):
        return f"remember how to {node.name}: {render_with_explicit_precedence(node.body)}"
    return render(node)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


_NEGATED_OPS = {
    "not_above": "not above",
    "not_below": "not below",
    "not_equal_to": "not equal to",
}
_OP_WORDS = {
    "above": "above",
    "below": "below",
    "equal_to": "equal to",
}


def _render_condition(node: ConditionNode) -> str:
    field = render(node.field)
    value = render(node.value)
    if node.op == "is":
        return f"{field} is {value}"
    if node.op in _OP_WORDS:
        return f"{field} is {_OP_WORDS[node.op]} {value}"
    if node.op in _NEGATED_OPS:
        return f"{field} is {_NEGATED_OPS[node.op]} {value}"
    raise ValueError(f"unknown condition operator '{node.op}'")


def _article_for(descriptor: str) -> str:
    """Return 'an' before vowel-initial descriptors, 'a' otherwise (v2a §71).

    Operates on the leading character of the first word of the descriptor.
    Multi-word descriptors (e.g., `remember a big number called ...`) are
    keyed on the first word, since that's what English speakers articulate.
    """
    if not descriptor:
        return "a"
    first = descriptor.split()[0] if descriptor.split() else descriptor
    return "an" if first[:1].lower() in "aeiou" else "a"


def _fmt_number(v: int | float) -> str:
    if isinstance(v, bool):
        # Defensive — booleans should not appear in v1 ASTs.
        return str(v)
    if isinstance(v, int):
        return str(v)
    if v.is_integer():
        return str(int(v))
    return str(v)


def _emit_string(s: str) -> str:
    """v2c §90 — conditional quoting. Emit quotes around a string value
    iff it contains a space (multi-word) or matches a reserved word.
    This preserves round-trip integrity: `with label as "filter"` keeps
    its quotes; `with status as active` stays bare.
    """
    if " " in s or s in ALL_RESERVED:
        return f'"{s}"'
    return s

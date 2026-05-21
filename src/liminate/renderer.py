"""Canonical prose renderer for Liminate v1 / v2c / v2d / v3a.

Sources:
- v1a §33 (canonical prose rendering is a parser output requirement —
  used for intent verification, obfuscation prevention, and round-trip
  fidelity).
- v1b §42 (display formats — separate concern, lives in interpreter).
- v3a §110 (action blocks use indentation; WhenNode renders multi-line).

The canonical rendering is the inverse of parsing: it walks the AST and
emits a paren-free English sentence in canonical slot order. Round-trip
property: `parse(tokenize(render(ast)))` must equal `ast`. For v3a
WhenNode this round-trip goes through the multi-line `parse_when_block`
path — the rendered output is a `when <cond>` header followed by
indented action lines (strictly multi-line, not a single line).

A second entry point — `render_with_explicit_precedence` — emits the
same AST with parenthesized compound conditions, used for the AMBER
precedence message (v1a §30, v1c §50 outcome 2). This rendering is not
required to round-trip through the parser.
"""

from __future__ import annotations

from .parser import (
    AboutNode,
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
    SequenceNode,
    ShowNode,
    SortNode,
    TransformNode,
    WeakensNode,
    WhenNode,
)
from .vocabulary import ALL_RESERVED


# v3a §110: action lines inside a `when` block are indented by two spaces
# in canonical form. The parser accepts any positive indent depth; the
# renderer commits to two-space indentation for consistency.
_WHEN_BLOCK_INDENT = "  "


def render(node: ASTNode) -> str:
    """Canonical (paren-free) prose rendering of an AST node.

    Meta-Structural Era batch 2: if the node carries a `because`
    rationale (an optional, inert metadata field present on every verb
    statement node), append the canonical `because "<rationale>"` clause.
    Sub-expression nodes (conditions, values) and `SequenceNode` have no
    `rationale` field, so the clause is only ever appended to a statement.
    A statement nested inside a sequence/choose/each/when action renders
    its own rationale through the recursive `render` call.
    """
    rendered = _render_node(node)
    rationale = getattr(node, "rationale", None)
    if rationale is not None:
        return f'{rendered} because "{rationale}"'
    return rendered


def _render_node(node: ASTNode) -> str:
    """Render an AST node without its `because` rationale (see `render`)."""
    if isinstance(node, AboutNode):
        # Meta-Structural Era: quote multi-word topics, leave a single
        # (e.g. hyphenated) word bare.
        if " " in node.topic:
            return f'about "{node.topic}"'
        return f"about {node.topic}"
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
    if isinstance(node, ArithmeticNode):
        # Infrastructure Era — paren-free flat prose. PEMDAS is implicit
        # in the canonical form, mirroring how humans read arithmetic.
        return f"{render(node.left)} {_ARITHMETIC_OP_WORDS[node.op]} {render(node.right)}"

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
        desc = node.descriptor or "list"
        art = _article_for(desc)
        if not node.items:
            return f"remember {art} {desc} called {node.name}"
        items = " and ".join(render(i) for i in node.items)
        return f"remember {art} {desc} called {node.name} with {items}"
    if isinstance(node, RememberRecordNode):
        fields = " and ".join(f"{n} as {render(v)}" for n, v in node.fields)
        desc = node.descriptor or "record"
        art = _article_for(desc)
        return f"remember {art} {desc} called {node.name} with {fields}"
    if isinstance(node, RememberCompositionNode):
        # v2d §96: emit `from <param>` between the composition name and
        # the colon when the definition declared a parameter.
        if node.param is not None:
            return (
                f"remember how to {node.name} from {node.param}: "
                f"{render(node.body)}"
            )
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
        # v2d §96: parameter-passing call form.
        if node.arg is not None:
            return f"{node.name} from {node.arg}"
        return node.name
    if isinstance(node, ChooseNode):
        return _render_choose(node)
    if isinstance(node, SequenceNode):
        return _render_sequence(node, render)

    if isinstance(node, WhenNode):
        # v3a §108–§110 canonical form:
        #   when <cond> [unless <guard>]
        #     <action-line-1>
        #     <action-line-2>
        #     ...
        # Action lines are two-space indented (§110 mandates ≥1 space;
        # the renderer commits to two for visual consistency). For a
        # single-statement action block the indented line is the lone
        # action; for SequenceNode actions, one line per operation.
        return _render_when(node, render)
    if isinstance(node, FinishNode):
        # v3a §112: `finish` is the verb leaf — no slots, no decoration.
        return "finish"
    if isinstance(node, AddNode):
        # Liminate `add` v1 §10 — canonical form: `add <item> to <list>`.
        return f"add {render(node.item)} to {node.target.name}"
    if isinstance(node, RemoveNode):
        # Canonical form: `remove <item> from <list>`.
        return f"remove {render(node.item)} from {node.target.name}"
    if isinstance(node, WeakensNode):
        # Metabolic Era batch 1 — `weakens <subject> over <period>`.
        return (
            f"weakens {node.subject.name} "
            f"over {_fmt_number(node.period.value)}"
        )
    if isinstance(node, RequireNode):
        # Normative Era batch 2 — `require <condition>`.
        return f"require {render(node.condition)}"
    if isinstance(node, ExpectNode):
        # Epistemic Era batch 3 — `expect <condition>`.
        return f"expect {render(node.condition)}"
    if isinstance(node, AssignNode):
        # Delegated Era batch 3 — `assign <item> to <recipient>`.
        return f"assign {node.item.name} to {render(node.recipient)}"
    if isinstance(node, SortNode):
        # Infrastructure Era batch 2 — canonical form keeps the natural
        # `in reverse` for descending; ascending is the default and
        # omits the modifier.
        base = f"sort the {node.target.name} by {node.field}"
        if node.descending:
            return f"{base} in reverse"
        return base
    if isinstance(node, CompareNode):
        # V2 promotion — `compare <left> to <right>`.
        return f"compare {render(node.left)} to {render(node.right)}"
    if isinstance(node, TransformNode):
        # Final V2 promotion — record-field mode renders the `<field> of`
        # prefix; scalar-list mode omits it.
        expr_str = render(node.expression)
        if node.field is not None:
            return (
                f"transform {node.field} of {render(node.target)} "
                f"by {expr_str}"
            )
        return f"transform {render(node.target)} by {expr_str}"

    if isinstance(node, PackVerbNode):
        # v4a §137 + v2: pack verbs render as `<word> [<conn>] <value>...`
        # in slot order. Positional slots (connective is None) render with
        # no preceding connective word. Empty optional slots are skipped.
        parts: list[str] = [node.word]
        for slot in node.signature.slots:
            if slot.name not in node.slot_values:
                continue
            if slot.connective is not None:
                parts.append(slot.connective)
            parts.append(render(node.slot_values[slot.name]))
        return " ".join(parts)

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
        return _render_sequence(node, render_with_explicit_precedence)
    if isinstance(node, RequireNode):
        return f"require {render_with_explicit_precedence(node.condition)}"
    if isinstance(node, ExpectNode):
        return f"expect {render_with_explicit_precedence(node.condition)}"
    if isinstance(node, AssignNode):
        return (
            f"assign {node.item.name} to "
            f"{render_with_explicit_precedence(node.recipient)}"
        )
    if isinstance(node, RememberCompositionNode):
        if node.param is not None:
            return (
                f"remember how to {node.name} from {node.param}: "
                f"{render_with_explicit_precedence(node.body)}"
            )
        return f"remember how to {node.name}: {render_with_explicit_precedence(node.body)}"
    if isinstance(node, ChooseNode):
        parts: list[str] = []
        for i, br in enumerate(node.branches):
            if i == 0:
                parts.append(
                    f"choose if {render_with_explicit_precedence(br.condition)}: "
                    f"{render_with_explicit_precedence(br.action)}"
                )
            elif br.condition is not None:
                parts.append(
                    f"otherwise if {render_with_explicit_precedence(br.condition)}: "
                    f"{render_with_explicit_precedence(br.action)}"
                )
            else:
                parts.append(
                    f"otherwise {render_with_explicit_precedence(br.action)}"
                )
        return " ".join(parts)
    if isinstance(node, WhenNode):
        # v3a §123 amber path — rendering with explicit parens lets the
        # user see how the parser grouped a mixed and/or `when` or
        # `unless` clause before they confirm.
        return _render_when(node, render_with_explicit_precedence)
    return render(node)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


_ARITHMETIC_OP_WORDS = {
    "plus": "plus",
    "minus": "minus",
    "multiplied_by": "multiplied by",
    "divided_by": "divided by",
}


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


def _render_choose(node: ChooseNode) -> str:
    """v2d §99/§101 — canonical form:
        choose if <c1>: <a1> [otherwise if <c2>: <a2>]... [otherwise <aN>]

    The first branch always carries an `if` (consumed by the verb). Each
    subsequent branch begins with `otherwise`; a branch with a condition
    adds `if <c>:`; a terminal branch (condition=None) is just `<action>`.
    """
    parts: list[str] = []
    for i, br in enumerate(node.branches):
        if i == 0:
            parts.append(f"choose if {render(br.condition)}: {render(br.action)}")
        elif br.condition is not None:
            parts.append(f"otherwise if {render(br.condition)}: {render(br.action)}")
        else:
            parts.append(f"otherwise {render(br.action)}")
    return " ".join(parts)


def _render_sequence(node: SequenceNode, render_fn) -> str:
    """Render a SequenceNode honoring its `connectors` metadata.

    Normative Era batch 2: joins use `and` or `then` per the original
    source. An empty `connectors` list (legacy callers that built a
    SequenceNode without specifying joins) falls back to `and`.
    """
    if not node.operations:
        return ""
    parts: list[str] = [render_fn(node.operations[0])]
    for i, op in enumerate(node.operations[1:]):
        conn = (
            node.connectors[i]
            if i < len(node.connectors)
            else "and"
        )
        parts.append(f" {conn} ")
        parts.append(render_fn(op))
    return "".join(parts)


def _render_when(node: WhenNode, render_fn) -> str:
    """v3a §108–§110 — canonical form:
        when <cond> [unless <guard>]
          <action-line-1>
          [<action-line-2>]
          ...

    `render_fn` is either `render` (paren-free) or
    `render_with_explicit_precedence` (parens around mixed and/or).
    Action lines are two-space indented; each operation in a
    SequenceNode action gets its own line. A single-statement action
    block produces exactly one indented line.
    """
    header = f"when {render_fn(node.condition)}"
    if node.unless is not None:
        header += f" unless {render_fn(node.unless)}"
    if isinstance(node.action, SequenceNode):
        action_lines = [render_fn(op) for op in node.action.operations]
    else:
        action_lines = [render_fn(node.action)]
    indented = "\n".join(f"{_WHEN_BLOCK_INDENT}{line}" for line in action_lines)
    return f"{header}\n{indented}"


def _render_condition(node: ConditionNode) -> str:
    field = render(node.field)
    value = render(node.value)
    if node.op == "is":
        return f"{field} is {value}"
    if node.op in _OP_WORDS:
        return f"{field} is {_OP_WORDS[node.op]} {value}"
    if node.op in _NEGATED_OPS:
        return f"{field} is {_NEGATED_OPS[node.op]} {value}"
    if node.op == "includes":
        return f"{field} includes {value}"
    if node.op == "not_includes":
        return f"{field} not includes {value}"
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
    iff dropping them would change the value on re-lex. That is true
    when:
      - the value contains a space (multi-word → bare form won't even
        tokenize as one token), or
      - the value matches a reserved word (bare form would be rejected
        as a verb/connective/etc.), or
      - the value differs from its lowercased form (case would be lost
        because the lexer normalizes unquoted words; quoted content is
        preserved verbatim).
    `with status as active` stays bare; `with status as "Active"` keeps
    its quotes.
    """
    if " " in s or s in ALL_RESERVED or s != s.lower():
        return f'"{s}"'
    return s

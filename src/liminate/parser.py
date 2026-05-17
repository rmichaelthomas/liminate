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

from dataclasses import dataclass, field
from typing import Any

from .result import LiminateResult, ResultStatus
from .vocabulary import (
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


@dataclass
class RememberListNode(ASTNode):
    name: str
    items: list[ASTNode]
    # v2a §71 / D6 — see RememberValueNode for rationale.
    descriptor: str | None = field(default=None, compare=False)


@dataclass
class RememberRecordNode(ASTNode):
    name: str
    fields: list[tuple[str, ASTNode]]
    # v2a §71 / D6 — see RememberValueNode for rationale.
    descriptor: str | None = field(default=None, compare=False)


@dataclass
class RememberCompositionNode(ASTNode):
    name: str
    body: ASTNode
    # v2d §96 — optional single named parameter. None when the composition
    # was defined without a `from <param>` clause (the v1/v2a/v2b/v2c shape).
    # The parameter name follows v1's name rules (UNKNOWN token, reserved-
    # word exclusion via _consume_name).
    param: str | None = None


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


@dataclass
class FilterNode(ASTNode):
    target: NameRef
    condition: ASTNode


@dataclass
class KeepNode(ASTNode):
    """v2a §67 — non-destructive sibling of FilterNode. Same shape: a
    target list and a condition. Difference is purely semantic: keep
    returns a new list without modifying the source's symbol-table
    entry. Compositions wrapping `keep` are reusable on the same data
    (resolving D3)."""
    target: NameRef
    condition: ASTNode


@dataclass
class CountNode(ASTNode):
    target: NameRef


@dataclass
class GatherNode(ASTNode):
    name: str
    from_val: int | float
    to_val: int | float


@dataclass
class CombineNode(ASTNode):
    target: NameRef


@dataclass
class EachNode(ASTNode):
    collection: NameRef
    action: ASTNode


@dataclass
class CompositionCallNode(ASTNode):
    name: str
    # v2d §96 — optional parameter-passing argument. None when the call
    # provided no `from <name>` clause. The argument is always a name
    # reference (names-only per §96); literal values are rejected at
    # parse time.
    arg: str | None = None


@dataclass
class SequenceNode(ASTNode):
    operations: list[ASTNode]


@dataclass
class ConditionNode(ASTNode):
    field: ASTNode               # NameRef or EachPronoun
    op: str                      # is, above, below, equal_to, not_above, not_below, not_equal_to
    value: ASTNode               # NumberLiteral, BareWord, NameRef, EachPronoun


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


@dataclass
class AddNode(ASTNode):
    """Liminate `add` v1 §10 — append an item to an existing list.

    `item` is the value being appended (NumberLiteral, BareWord, NameRef,
    QuotedString, or FieldAccessNode — same value types accepted by
    `remember ... with`). `target` is the list receiving the item.
    """
    item: ASTNode
    target: NameRef


@dataclass
class FinishNode(ASTNode):
    """v3a §112 — exit listener mode immediately and totally.

    No slots. Legal only inside a `when` action block (directly, inside
    a `choose` branch, or inside a composition called from an action
    block). `finish` during Phase 1 is a semantic error.
    """
    pass


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


def _parse_operation_sequence(stream: TokenStream, comp: set[str]) -> ASTNode:
    first = _parse_one_operation(stream, comp)
    operations: list[ASTNode] = [first]
    while not stream.at_end():
        peek = stream.peek()
        if not (peek and peek.type is TokenType.CONNECTIVE and peek.value == "and"):
            break
        nxt = stream.peek(1)
        if not (nxt and nxt.type is TokenType.VERB):
            break
        stream.consume()  # eat `and`
        operations.append(_parse_one_operation(stream, comp))
    if len(operations) == 1:
        return operations[0]
    return SequenceNode(operations=operations)


def _parse_one_operation(stream: TokenStream, comp: set[str]) -> ASTNode:
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
        raise _ParseError(
            "I don't recognize a command here. Every sentence needs a verb "
            "like 'remember', 'show', 'filter', 'count', 'gather', "
            "'combine', 'each', or 'choose'."
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
    if verb.value == "combine":
        return _parse_combine(stream)
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
       next token is VERB  -> result capture via recursive descent
       next token is UNKNOWN -> simple reference (copy semantics)
    """
    peek = stream.peek()
    if peek is None:
        raise _ParseError("I expected an expression after 'from'.")
    if peek.type is TokenType.VERB:
        sub = _parse_verb_statement(stream, comp)
        return RememberValueNode(name=name, value=sub, descriptor=descriptor)
    if peek.type is TokenType.UNKNOWN:
        # Could be a composition call (v1b §41 fallback inside the from-expr).
        if peek.value in comp:
            stream.consume()
            # v2d §98 — peek-ahead for parameterized call in value-capture
            # position. `remember the r called r from find-big from orders`
            # has two `from` tokens: the outer is value capture, the inner
            # is parameter passing. Since parameters are names-only (§96),
            # `from UNKNOWN` after a known composition is always param-
            # passing.
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
        stream.consume()
        # v2b §77: `from <field> of <record>` — field-access value.
        after = stream.peek()
        if after and after.type is TokenType.CONNECTIVE and after.value == "of":
            access = _maybe_field_access(stream, peek.value)
            return RememberValueNode(name=name, value=access, descriptor=descriptor)
        return RememberValueNode(
            name=name, value=NameRef(name=peek.value), descriptor=descriptor,
        )
    cat = reserved_category(peek.value)
    if cat:
        raise _ParseError(
            f"The word '{peek.value}' is reserved in Liminate — "
            f"it's used as a {cat} and can't be used as a value."
        )
    raise _ParseError(f"I didn't expect '{peek.value}' after 'from'.")


# ---------------------------------------------------------------------------
# show / count / combine
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


def _parse_combine(stream: TokenStream) -> CombineNode:
    _consume_optional_article(stream)
    target = _consume_target(stream, verb="combine")
    return CombineNode(target=target)


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

    return GatherNode(name=name, from_val=from_val, to_val=to_val)


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
    head = stream.consume()
    if head is None:
        raise _ParseError("I expected a field after 'where'.")
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

    is_tok = stream.consume()
    if not (is_tok and is_tok.type is TokenType.OPERATOR and is_tok.value == "is"):
        raise _ParseError("I expected 'is' in this condition.")

    # `is` is a comparison introducer if next token is a known operator
    # (above/below/equal_to/not); otherwise `is` itself is equality (§21).
    nxt = stream.peek()
    if nxt is None:
        raise _ParseError("I expected a value or comparison after 'is'.")

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


# ---------------------------------------------------------------------------
# Value parsing (literals + name references)
# ---------------------------------------------------------------------------


def _parse_value(stream: TokenStream) -> ASTNode:
    """Consume a single value token (NUMBER, UNKNOWN, or QUOTED_STRING),
    optionally extended by `of <record>` for field access (v2b §77).

    Vocabulary words in value position are rejected per v1c §46 (extended
    by v2c §89 — the error message now suggests quoting as the fix).
    """
    tok = stream.consume()
    if tok is None:
        raise _ParseError("I expected a value here.")
    if tok.type is TokenType.NUMBER:
        return NumberLiteral(value=_parse_number(tok.value))
    if tok.type is TokenType.UNKNOWN:
        # v2b §77: `<field> of <record>` field-access value expression.
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


def _consume_parameter_arg(stream: TokenStream, *, comp_name: str) -> str:
    """v2d §96 — consume the name token that follows `<comp> from` at a
    call site. Names-only: NUMBER / QUOTED_STRING / reserved words are
    rejected here at parse time. The actual symbol lookup happens at run
    time, consistent with v1's name-resolution timing (inception §23).
    """
    tok = stream.consume()
    if tok is None:
        raise _ParseError(
            f"I expected a name after '{comp_name} from' — "
            f"compositions take a single name as input."
        )
    if tok.type is TokenType.QUOTED_STRING:
        raise _ParseError(
            f"Names can't have spaces. Try a hyphenated name like "
            f"'{_hyphenate(tok.value)}' instead."
        )
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

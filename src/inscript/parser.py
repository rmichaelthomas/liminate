"""Parser for Inscript v1.

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
- An InscriptResult on amber (mixed-precedence) or parse error.

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

from .result import InscriptResult, ResultStatus
from .vocabulary import (
    Token,
    TokenType,
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


@dataclass
class RememberListNode(ASTNode):
    name: str
    items: list[ASTNode]


@dataclass
class RememberRecordNode(ASTNode):
    name: str
    fields: list[tuple[str, ASTNode]]


@dataclass
class RememberCompositionNode(ASTNode):
    name: str
    body: ASTNode


@dataclass
class ShowNode(ASTNode):
    target: ASTNode | None  # None = display the current iterator item


@dataclass
class FilterNode(ASTNode):
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
) -> ASTNode | InscriptResult:
    """Parse a canonically-ordered token list into an AST.

    Returns:
        - ASTNode on success.
        - InscriptResult with status AMBER_PRECEDENCE if a `where` clause
          uses both `and` and `or` (v1a §30). The pending AST is attached
          so the caller can resume after confirmation.
        - InscriptResult with status ERROR_PARSE on any other parse failure.
    """
    if not tokens:
        return InscriptResult(
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
        return InscriptResult(
            status=ResultStatus.ERROR_PARSE,
            message=e.message,
            executed=False,
        )

    # v1a §30: mixed and/or in any `where` clause -> AMBER_PRECEDENCE.
    if _contains_mixed_precedence(ast):
        from .renderer import render, render_with_explicit_precedence
        return InscriptResult(
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
            return CompositionCallNode(name=t.value)
        raise _ParseError(
            "I don't recognize a command here. Every sentence needs a verb "
            "like 'remember', 'show', 'filter', 'count', 'gather', "
            "'combine', or 'each'."
        )
    raise _ParseError(f"I didn't expect '{t.value}' at the start of an operation.")


def _parse_verb_statement(stream: TokenStream, comp: set[str]) -> ASTNode:
    verb = stream.consume()
    if verb.value == "remember":
        return _parse_remember(stream, comp)
    if verb.value == "show":
        return _parse_show(stream)
    if verb.value == "filter":
        return _parse_filter(stream)
    if verb.value == "count":
        return _parse_count(stream)
    if verb.value == "gather":
        return _parse_gather(stream)
    if verb.value == "combine":
        return _parse_combine(stream)
    if verb.value == "each":
        return _parse_each(stream, comp)
    raise _ParseError(f"Unknown verb '{verb.value}'.")


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

    descriptor = _consume_remember_intro(stream)

    called = stream.consume()
    if not (called and called.type is TokenType.CONNECTIVE and called.value == "called"):
        raise _ParseError(
            "I expected the word 'called' to introduce the name."
        )

    name = _consume_name(stream, after="'called'")

    intro = stream.consume()
    if intro is None:
        raise _ParseError(f"I expected 'with' or 'from' after '{name}'.")
    if intro.type is not TokenType.CONNECTIVE or intro.value not in ("with", "from"):
        raise _ParseError(f"I expected 'with' or 'from', not '{intro.value}'.")

    if intro.value == "with":
        return _parse_remember_with(stream, name, descriptor)
    return _parse_remember_from(stream, name, comp)


def _parse_composition_definition(stream: TokenStream, comp: set[str]) -> RememberCompositionNode:
    stream.consume()  # how
    to = stream.consume()
    if not (to and to.type is TokenType.CONNECTIVE and to.value == "to"):
        raise _ParseError("I expected 'to' after 'how'.")

    name = _consume_name(stream, after="'how to'")

    colon = stream.consume()
    if not (colon and colon.type is TokenType.DELIMITER and colon.value == ":"):
        raise _ParseError("I expected ':' after the composition name.")

    body = _parse_operation_sequence(stream, comp)
    return RememberCompositionNode(name=name, body=body)


def _consume_remember_intro(stream: TokenStream) -> str | None:
    """Consume zero+ articles and zero+ descriptor UNKNOWNs before `called`.

    Returns the captured descriptor `list` if it appeared (used to force
    list construction for singleton `with X`); other descriptors are
    discarded as decorative per v1b §36.
    """
    descriptor: str | None = None
    while True:
        t = stream.peek()
        if t is None:
            raise _ParseError("I expected 'called' to introduce the name.")
        if t.type is TokenType.CONNECTIVE and t.value == "called":
            return descriptor
        if t.type is TokenType.ARTICLE:
            stream.consume()
            continue
        if t.type is TokenType.UNKNOWN:
            if t.value == "list":
                descriptor = "list"
            stream.consume()
            continue
        # Vocabulary word at a position that should have been a descriptor.
        cat = reserved_category(t.value)
        if cat:
            raise _ParseError(
                f"The word '{t.value}' is reserved in Inscript — "
                f"it's used as a {cat}. Please choose a different name."
            )
        raise _ParseError(f"I didn't expect '{t.value}' before 'called'.")


def _parse_remember_with(
    stream: TokenStream, name: str, descriptor: str | None,
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
        return RememberRecordNode(name=name, fields=fields)

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

    if is_list:
        return RememberListNode(name=name, items=items)
    if descriptor == "list":
        return RememberListNode(name=name, items=items)
    return RememberValueNode(name=name, value=items[0])


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
    if field_tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(field_tok.value)
        if cat:
            raise _ParseError(
                f"The word '{field_tok.value}' is reserved in Inscript — "
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


def _parse_remember_from(stream: TokenStream, name: str, comp: set[str]) -> ASTNode:
    """`from` in `remember` (v1b §43):
       next token is VERB  -> result capture via recursive descent
       next token is UNKNOWN -> simple reference (copy semantics)
    """
    peek = stream.peek()
    if peek is None:
        raise _ParseError("I expected an expression after 'from'.")
    if peek.type is TokenType.VERB:
        sub = _parse_verb_statement(stream, comp)
        return RememberValueNode(name=name, value=sub)
    if peek.type is TokenType.UNKNOWN:
        # Could be a composition call (v1b §41 fallback inside the from-expr).
        if peek.value in comp:
            stream.consume()
            return RememberValueNode(name=name, value=CompositionCallNode(name=peek.value))
        stream.consume()
        return RememberValueNode(name=name, value=NameRef(name=peek.value))
    cat = reserved_category(peek.value)
    if cat:
        raise _ParseError(
            f"The word '{peek.value}' is reserved in Inscript — "
            f"it's used as a {cat} and can't be used as a value."
        )
    raise _ParseError(f"I didn't expect '{peek.value}' after 'from'.")


# ---------------------------------------------------------------------------
# show / count / combine
# ---------------------------------------------------------------------------


def _parse_show(stream: TokenStream) -> ShowNode:
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
    if peek.type is TokenType.UNKNOWN:
        stream.consume()
        return ShowNode(target=NameRef(name=peek.value))
    cat = reserved_category(peek.value)
    if cat:
        if peek.value == "each":
            raise _ParseError(
                "'each' is a verb in Inscript — it iterates a list, or "
                "acts as a self-reference pronoun inside a 'where' "
                "clause. It can't appear as a target on its own."
            )
        raise _ParseError(
            f"I expected a target after 'show', but '{peek.value}' is a "
            f"{cat} in Inscript. Targets must be names you've created "
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
                f"The word '{name_tok.value}' is reserved in Inscript — "
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
                f"'{coll_tok.value}' is a {cat} in Inscript. Collections "
                f"must be names you've created with 'remember' or 'gather'."
            )
        raise _ParseError(f"I expected a collection after 'each'.")
    collection = NameRef(name=coll_tok.value)

    if stream.at_end():
        raise _ParseError("I expected an action for 'each'.")

    stream.push_clause("each")
    try:
        action = _parse_one_operation(stream, comp)
    finally:
        stream.pop_clause()
    return EachNode(collection=collection, action=action)


# ---------------------------------------------------------------------------
# filter + where conditions
# ---------------------------------------------------------------------------


def _parse_filter(stream: TokenStream) -> FilterNode:
    _consume_optional_article(stream)
    target = _consume_target(stream, verb="filter")

    where_tok = stream.consume()
    if not (where_tok and where_tok.type is TokenType.CONNECTIVE and where_tok.value == "where"):
        raise _ParseError("I expected 'where' to introduce the condition.")

    stream.push_clause("where")
    try:
        condition = _parse_or_condition(stream)
    finally:
        stream.pop_clause()
    return FilterNode(target=target, condition=condition)


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
        field_node = NameRef(name=head.value)
    else:
        cat = reserved_category(head.value)
        if cat:
            raise _ParseError(
                f"The word '{head.value}' is reserved in Inscript — "
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
    """Consume a single value token (NUMBER or UNKNOWN).

    Vocabulary words in value position are rejected per v1c §46.
    """
    tok = stream.consume()
    if tok is None:
        raise _ParseError("I expected a value here.")
    if tok.type is TokenType.NUMBER:
        return NumberLiteral(value=_parse_number(tok.value))
    if tok.type is TokenType.UNKNOWN:
        return BareWord(word=tok.value)
    cat = reserved_category(tok.value)
    if cat:
        raise _ParseError(
            f"The word '{tok.value}' is a {cat} in Inscript and can't be "
            f"used as a value. Try a different word."
        )
    raise _ParseError(f"I didn't expect '{tok.value}' as a value.")


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
    if tok is None:
        raise _ParseError(f"I expected a target after '{verb}'.")
    if tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(tok.value)
        if cat:
            # 'each' is both a verb and the in-`where` pronoun (v1b §37) —
            # surface that distinction when it appears as a target.
            if tok.value == "each":
                raise _ParseError(
                    "'each' is a verb in Inscript — it iterates a list, or "
                    "acts as a self-reference pronoun inside a 'where' "
                    "clause. It can't appear as a target on its own."
                )
            raise _ParseError(
                f"I expected a target after '{verb}', but '{tok.value}' "
                f"is a {cat} in Inscript. Targets must be names you've "
                f"created with 'remember' or 'gather'."
            )
        raise _ParseError(f"I expected a target after '{verb}', not '{tok.value}'.")
    return NameRef(name=tok.value)


def _consume_name(stream: TokenStream, *, after: str) -> str:
    tok = stream.consume()
    if tok is None:
        raise _ParseError(f"I expected a name after {after}.")
    if tok.type is not TokenType.UNKNOWN:
        cat = reserved_category(tok.value)
        if cat:
            raise _ParseError(
                f"The word '{tok.value}' is reserved in Inscript — "
                f"it's used as a {cat}. Please choose a different name."
            )
        raise _ParseError(f"I expected a name after {after}, not '{tok.value}'.")
    return tok.value


def _contains_mixed_precedence(node: ASTNode) -> bool:
    """Return True if any condition tree in `node` mixes `and` with `or`."""
    if isinstance(node, FilterNode):
        return _condition_is_mixed(node.condition)
    if isinstance(node, SequenceNode):
        return any(_contains_mixed_precedence(op) for op in node.operations)
    if isinstance(node, EachNode):
        return _contains_mixed_precedence(node.action)
    if isinstance(node, RememberCompositionNode):
        return _contains_mixed_precedence(node.body)
    if isinstance(node, RememberValueNode) and isinstance(node.value, ASTNode):
        return _contains_mixed_precedence(node.value)
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

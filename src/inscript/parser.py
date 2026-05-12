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
            # Composition chaining (`<name> from <name>`) is deferred to v2
            # alongside composition parameters (v1b §41, Q9). v2a §70: detect
            # this case and emit the specific deferral message rather than
            # the generic "I didn't expect 'from' here."
            after = stream.peek()
            if after and after.type is TokenType.CONNECTIVE and after.value == "from":
                raise _ParseError(
                    f"Composition chaining isn't supported yet. "
                    f"Call '{t.value}' on its own line."
                )
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

    descriptor, saw_list = _consume_remember_intro(stream)

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
        return _parse_remember_with(stream, name, descriptor, saw_list)
    return _parse_remember_from(stream, name, comp, descriptor)


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
                f"The word '{t.value}' is reserved in Inscript — "
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
            f"The word '{peek.value}' is reserved in Inscript — "
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
                        f"Inscript — it's used as a {rcat} and can't be "
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
        # v2a §69: the show parser keys multi-field detection off this
        # clause-context flag — see _parse_verb_statement / _parse_show.
        action = _parse_one_operation(stream, comp)
    finally:
        stream.pop_clause()
    return EachNode(collection=collection, action=action)


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
            f"The word '{tok.value}' is a {cat} in Inscript and can't be "
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
                f"Inscript — it's used as a {rcat} and can't be "
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
                f"The word '{tok.value}' is reserved in Inscript — "
                f"it's used as a {cat}. Please choose a different name."
            )
        raise _ParseError(f"I expected a name after {after}, not '{tok.value}'.")
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

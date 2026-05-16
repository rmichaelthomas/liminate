"""Phase 4 gate tests: renderer (v1a §33, v3a §110).

Verifies:
  1. Each AST node renders to a sensible canonical sentence.
  2. Round-trip: parse(tokenize(render(ast))) == ast for every locked
     parseable sentence.
  3. `render_with_explicit_precedence` parenthesizes mixed-precedence
     compound conditions for the AMBER message (v1a §30).
  4. v3a §110: WhenNode renders multi-line with two-space indentation;
     round-trips through `parse_when_block` (split-by-indent).
"""

import pytest

from liminate.lexer import tokenize
from liminate.parser import (
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
    FinishNode,
    GatherNode,
    NameRef,
    NumberLiteral,
    QuotedString,
    RememberCompositionNode,
    RememberListNode,
    RememberRecordNode,
    RememberValueNode,
    SequenceNode,
    ShowNode,
    WhenNode,
    parse,
    parse_when_block,
)
from liminate.renderer import render, render_with_explicit_precedence
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus


def _parse(line: str, comps=None):
    return parse(tokenize(line), composition_names=comps)


# ---------- direct renderings ----------

def test_render_number_literal():
    assert render(NumberLiteral(30)) == "30"
    assert render(NumberLiteral(3.14)) == "3.14"
    assert render(NumberLiteral(75.0)) == "75"  # integer-valued floats lose .0


def test_render_bareword_and_nameref():
    assert render(BareWord("active")) == "active"
    assert render(NameRef("orders")) == "orders"
    assert render(EachPronoun()) == "each"


def test_render_quoted_string_with_uppercase_keeps_quotes():
    """Quoted strings now preserve case. The renderer must keep quotes
    around any string that contains uppercase characters — without them,
    the value would be re-lexed in lowercase and the round-trip would
    silently corrupt the stored value (e.g. proper nouns, IDs).
    Single-word lowercase non-reserved values continue to emit bare."""
    assert render(QuotedString("Active")) == '"Active"'
    assert render(QuotedString("LosAngeles")) == '"LosAngeles"'
    assert render(QuotedString("active")) == "active"


def test_render_bareword_with_uppercase_keeps_quotes():
    """Same rule applies to BareWord nodes — if the stored value carries
    case that would be lost on re-lex, emit it quoted."""
    assert render(BareWord("Active")) == '"Active"'


def test_render_show():
    assert render(ShowNode(target=NameRef("age"))) == "show age"
    assert render(ShowNode(target=None)) == "show"


def test_render_filter_above():
    ast = FilterNode(
        target=NameRef("orders"),
        condition=ConditionNode(NameRef("total"), "above", NumberLiteral(50)),
    )
    assert render(ast) == "filter the orders where total is above 50"


def test_render_filter_equality():
    ast = FilterNode(
        target=NameRef("orders"),
        condition=ConditionNode(NameRef("status"), "is", BareWord("active")),
    )
    assert render(ast) == "filter the orders where status is active"


def test_render_filter_each_not_above():
    ast = FilterNode(
        target=NameRef("scores"),
        condition=ConditionNode(EachPronoun(), "not_above", NumberLiteral(7)),
    )
    assert render(ast) == "filter the scores where each is not above 7"


def test_render_filter_not_equal_to():
    ast = FilterNode(
        target=NameRef("scores"),
        condition=ConditionNode(EachPronoun(), "not_equal_to", NumberLiteral(5)),
    )
    assert render(ast) == "filter the scores where each is not equal to 5"


def test_render_filter_equal_to():
    ast = FilterNode(
        target=NameRef("orders"),
        condition=ConditionNode(NameRef("total"), "equal_to", NumberLiteral(75)),
    )
    assert render(ast) == "filter the orders where total is equal to 75"


def test_render_count_and_combine_and_gather():
    assert render(CountNode(target=NameRef("colors"))) == "count the colors"
    assert render(CombineNode(target=NameRef("numbers"))) == "combine the numbers"
    assert render(GatherNode("numbers", 1, 10)) == "gather the numbers from 1 to 10"


def test_render_each():
    ast = EachNode(
        collection=NameRef("orders"),
        action=ShowNode(target=NameRef("total")),
    )
    assert render(ast) == "each the orders show total"


def test_render_remember_value():
    ast = RememberValueNode(name="age", value=NumberLiteral(30))
    assert render(ast) == "remember a value called age with 30"


def test_render_remember_list():
    ast = RememberListNode(
        name="colors",
        items=[BareWord("red"), BareWord("blue")],
    )
    assert render(ast) == "remember a list called colors with red and blue"


def test_render_remember_record():
    ast = RememberRecordNode(
        name="order1",
        fields=[("total", NumberLiteral(75)), ("status", BareWord("active"))],
    )
    assert render(ast) == "remember a record called order1 with total as 75 and status as active"


def test_render_remember_composition():
    body = FilterNode(
        target=NameRef("orders"),
        condition=ConditionNode(NameRef("total"), "above", NumberLiteral(50)),
    )
    ast = RememberCompositionNode(name="find-big-orders", body=body)
    assert (
        render(ast)
        == "remember how to find-big-orders: filter the orders where total is above 50"
    )


def test_render_sequence():
    ast = SequenceNode(operations=[
        FilterNode(
            target=NameRef("orders"),
            condition=ConditionNode(NameRef("status"), "is", BareWord("active")),
        ),
        CountNode(target=NameRef("orders")),
    ])
    assert render(ast) == (
        "filter the orders where status is active and count the orders"
    )


def test_render_composition_call():
    assert render(CompositionCallNode("find-big-orders")) == "find-big-orders"


# ---------- compound conditions ----------

def test_render_compound_and_chain():
    cond = CompoundConditionNode(
        left=ConditionNode(NameRef("total"), "above", NumberLiteral(50)),
        right=ConditionNode(NameRef("status"), "is", BareWord("active")),
        connector="and",
    )
    ast = FilterNode(target=NameRef("orders"), condition=cond)
    assert render(ast) == (
        "filter the orders where total is above 50 and status is active"
    )


def test_render_compound_or_chain():
    cond = CompoundConditionNode(
        left=ConditionNode(NameRef("total"), "below", NumberLiteral(30)),
        right=ConditionNode(NameRef("status"), "is", BareWord("pending")),
        connector="or",
    )
    ast = FilterNode(target=NameRef("orders"), condition=cond)
    assert render(ast) == (
        "filter the orders where total is below 30 or status is pending"
    )


def test_render_canonical_is_paren_free_even_with_mixed_precedence():
    # The canonical form must remain re-parseable; no parens allowed.
    inner = CompoundConditionNode(
        left=ConditionNode(NameRef("total"), "above", NumberLiteral(50)),
        right=ConditionNode(NameRef("status"), "is", BareWord("active")),
        connector="and",
    )
    mixed = CompoundConditionNode(
        left=inner,
        right=ConditionNode(NameRef("status"), "is", BareWord("pending")),
        connector="or",
    )
    rendered = render(FilterNode(target=NameRef("orders"), condition=mixed))
    assert "(" not in rendered and ")" not in rendered


def test_explicit_precedence_renders_parens_for_mixed_clause():
    inner = CompoundConditionNode(
        left=ConditionNode(NameRef("total"), "above", NumberLiteral(50)),
        right=ConditionNode(NameRef("status"), "is", BareWord("active")),
        connector="and",
    )
    mixed = CompoundConditionNode(
        left=inner,
        right=ConditionNode(NameRef("status"), "is", BareWord("pending")),
        connector="or",
    )
    rendered = render_with_explicit_precedence(
        FilterNode(target=NameRef("orders"), condition=mixed)
    )
    assert "(total is above 50 and status is active) or status is pending" in rendered


# ---------- round-trip property ----------

ROUND_TRIP_SENTENCES = [
    # Program 1
    ("remember a number called age with 30", None),
    ("remember a list called colors with red and blue and green", None),
    ("show age", None),
    ("show colors", None),
    ("count the colors", None),
    # Program 2
    ("remember an order called order1 with total as 75 and status as active", None),
    ("remember a list called orders with order1 and order2 and order3", None),
    ("each the orders show total", None),
    # Program 3
    ("filter the orders where total is above 50", None),
    ("filter the orders where status is active", None),
    ("each the orders show status", None),
    # Program 4
    ("gather the numbers from 1 to 10", None),
    ("filter the numbers where each is above 5", None),
    ("combine the numbers", None),
    ("remember the result called total from combine the numbers", None),
    # Program 5 — not operator
    ("filter the scores where each is not above 7", None),
    ("filter the scores where each is not below 3", None),
    ("filter the scores where each is not equal to 5", None),
    # Compound + equality
    ("filter the orders where total is above 50 and status is active", None),
    ("filter the orders where total is below 30 or status is pending", None),
    ("filter the orders where total is equal to 75", None),
    # Compositions
    ("remember how to find-big-orders: filter the orders where total is above 50", None),
    ("remember how to count-active: filter the orders where status is active and count the orders", None),
    # Composition call
    ("show-missing", {"show-missing"}),
    # v1c addition
    ("remember an item called widget with 25", None),
    # Each pronoun + sequencing
    ("filter nums where each is above 3 and show missingname", None),
    # Single-item list (v1d sentence 38)
    ("remember a list called orders with order1", None),
    # v2d §96/§98 — composition parameters
    (
        "remember how to find-big from data: keep the data where total is above 50",
        None,
    ),
    ("find-big from orders", {"find-big"}),
    (
        "remember the results called big from find-big from orders",
        {"find-big"},
    ),
    # v2d §99/§101 — choose. Single-word literal strings can't round-trip
    # through `show <target>` because v2c §90's conditional quoting drops
    # them and re-parsing reads them as NameRefs. Use multi-word literals
    # in these cases so quoting survives the round-trip.
    ('choose if score is above 50: show "big order"', None),
    (
        'choose if score is above 50: show "big order" otherwise show "small order"',
        None,
    ),
    (
        'choose if level is above 8: show "very high" '
        'otherwise if level is above 3: show "medium range" '
        'otherwise show "very low"',
        None,
    ),
    # Multi-statement actions with multi-word literals.
    (
        'choose if score is above 50: show "big order" and '
        'count the orders '
        'otherwise show "small order" and '
        'count the orders',
        None,
    ),
    # `of` on the left side of a condition (v2d §100)
    ('choose if total of o1 is above 50: show "big order"', None),
]


@pytest.mark.parametrize("line,comps", ROUND_TRIP_SENTENCES)
def test_round_trip(line, comps):
    first_ast = _parse(line, comps=comps)
    assert not isinstance(first_ast, LiminateResult), f"first parse returned {first_ast}"

    rendered = render(first_ast)
    second_ast = _parse(rendered, comps=comps)
    assert not isinstance(second_ast, LiminateResult), (
        f"re-parse of canonical form failed: {rendered} -> {second_ast}"
    )
    assert second_ast == first_ast, (
        f"round-trip mismatch:\n  original: {line!r}\n  canonical: {rendered!r}\n"
        f"  first AST: {first_ast}\n  second AST: {second_ast}"
    )


# ---------- mixed-precedence amber still produces a canonical rendering ----------

def test_amber_result_carries_paren_free_canonical():
    result = _parse(
        "filter the orders where total is above 50 and status is active or status is pending"
    )
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.AMBER_PRECEDENCE
    assert result.canonical is not None
    assert "(" not in result.canonical and ")" not in result.canonical


# ---------- v3a §110/§112: WhenNode and FinishNode ----------


def test_render_finish_node():
    """v3a §112: `finish` renders as the bare verb leaf."""
    assert render(FinishNode()) == "finish"


def test_render_when_single_action():
    """v3a §110: header on first line, action indented two spaces.

    Multi-word literal kept here so v2c §90 conditional quoting (which
    strips quotes from single-word non-reserved values) doesn't make the
    rendered form ambiguous."""
    node = WhenNode(
        condition=ConditionNode(
            field=NameRef("temperature"), op="above", value=NumberLiteral(100),
        ),
        unless=None,
        action=ShowNode(target=QuotedString("high alert")),
    )
    assert render(node) == 'when temperature is above 100\n  show "high alert"'


def test_render_when_with_unless_guard():
    """v3a §109: `unless` appears inline on the header line."""
    node = WhenNode(
        condition=ConditionNode(
            field=NameRef("temperature"), op="above", value=NumberLiteral(100),
        ),
        unless=ConditionNode(
            field=NameRef("silenced"), op="equal_to", value=BareWord("true"),
        ),
        action=ShowNode(target=QuotedString("high alert")),
    )
    rendered = render(node)
    assert "when temperature is above 100" in rendered
    assert "unless silenced is equal to true" in rendered
    assert '  show "high alert"' in rendered


def test_render_when_multi_statement_action_block():
    """v3a §110: SequenceNode actions render one indented line per
    operation, preserving block structure."""
    node = WhenNode(
        condition=ConditionNode(
            field=NameRef("level"), op="above", value=NumberLiteral(50),
        ),
        unless=None,
        action=SequenceNode(operations=[
            ShowNode(target=QuotedString("very high")),
            RememberValueNode(name="status", value=BareWord("active")),
        ]),
    )
    rendered = render(node)
    lines = rendered.split("\n")
    assert lines[0] == "when level is above 50"
    assert lines[1].startswith("  ") and 'show "very high"' in lines[1]
    assert lines[2].startswith("  ") and "remember" in lines[2]


def test_render_when_with_finish_action():
    """v3a §112: `finish` as the action body renders cleanly."""
    node = WhenNode(
        condition=ConditionNode(
            field=NameRef("level"), op="above", value=NumberLiteral(2),
        ),
        unless=None,
        action=FinishNode(),
    )
    assert render(node) == "when level is above 2\n  finish"


def test_render_when_with_explicit_precedence_parenthesizes_mixed():
    """v3a §123 amber: mixed and/or in a `when` condition is rendered
    with parens so the user sees how the parser grouped them.

    (Uses `score`/`level`/`humidity` rather than `a`/`b`/`c` because
    `a` is an article in Liminate — reserved words can't appear as
    field names.)"""
    node = WhenNode(
        condition=CompoundConditionNode(
            left=CompoundConditionNode(
                left=ConditionNode(NameRef("score"), "above", NumberLiteral(1)),
                right=ConditionNode(NameRef("level"), "above", NumberLiteral(2)),
                connector="and",
            ),
            right=ConditionNode(NameRef("humidity"), "above", NumberLiteral(3)),
            connector="or",
        ),
        unless=None,
        action=ShowNode(target=QuotedString("high alert")),
    )
    rendered = render_with_explicit_precedence(node)
    # The (left AND right) group is rendered with parens since its
    # connector differs from the outer OR — mirroring v1a §30.
    assert "(score is above 1 and level is above 2)" in rendered
    assert " or humidity is above 3" in rendered


def _round_trip_when(header: str, *actions: str) -> tuple[ASTNode, str]:
    """Parse a `when` block, render it, then re-parse the rendering by
    splitting it back into header + indented action lines (v3a §110
    round-trip path)."""
    header_tokens = reorder(tokenize(header))
    action_lists = [reorder(tokenize(a)) for a in actions]
    first = parse_when_block(header_tokens, action_lists)
    assert not isinstance(first, LiminateResult), f"first parse: {first}"

    rendered = render(first)
    lines = rendered.split("\n")
    re_header = reorder(tokenize(lines[0]))
    re_actions = []
    for line in lines[1:]:
        stripped = line.lstrip(" ")
        if not stripped:
            continue
        re_actions.append(reorder(tokenize(stripped)))
    second = parse_when_block(re_header, re_actions)
    assert not isinstance(second, LiminateResult), f"re-parse: {second}"
    assert second == first, f"\n  rendered: {rendered!r}\n  first: {first}\n  second: {second}"
    return first, rendered


def test_when_round_trip_single_action():
    # Multi-word literal — v2c §90 conditional quoting otherwise drops
    # quotes off a single-word show target and re-parses it as NameRef,
    # breaking the AST round-trip.
    _round_trip_when("when temperature is above 100", 'show "high alert"')


def test_when_round_trip_with_unless():
    _round_trip_when(
        "when temperature is above 100 unless silenced is equal to true",
        'show "high alert"',
    )


def test_when_round_trip_multi_statement():
    _round_trip_when(
        "when level is above 50",
        'show "very high"',
        "remember a string called status with active",
    )


def test_when_round_trip_with_choose_action():
    _round_trip_when(
        "when temperature is above 100",
        'choose if mode is equal to silent: show "silent mode" '
        'otherwise show "loud alert"',
    )


def test_when_round_trip_with_finish():
    _round_trip_when("when level is above 2", "finish")

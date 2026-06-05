"""Phase 2 D-1 — composition parameters accept literal values.

Compositions may now be called with a numeric literal or a quoted-string
literal as the single parameter argument, alongside the existing bare-name
form. Literals are self-contained atoms: no symbol-table lookup, no
arithmetic, no `of` field access. Bare names keep their v2d §96 semantics.
"""

from liminate.cli import Session
from liminate.parser import (
    CompositionCallNode,
    NumberLiteral,
    QuotedString,
    parse,
)
from liminate.lexer import tokenize
from liminate.renderer import render
from liminate.result import LiminateResult, ResultStatus


def run_lines(lines):
    session = Session()
    results = [session.run_line(line) for line in lines]
    return session, results


def parse_line(line, comps=None):
    # Parse directly (no reorderer) so parser-level rejection paths — e.g. a
    # reserved word as an argument — are reached as units, matching
    # tests/test_parser.py. The reorderer would otherwise intercept a leading
    # verb token before the parser sees it.
    return parse(tokenize(line), composition_names=comps or set())


# ---------------------------------------------------------------------------
# 1–3, 14 — literal params execute correctly through the full pipeline
# ---------------------------------------------------------------------------


def test_numeric_literal_parameter_used_in_body():
    """1. `find-big from 50` — numeric literal bound to the param, the
    composition body references it as a threshold."""
    session, results = run_lines([
        "remember an order called o1 with total as 75 and status as active",
        "remember an order called o2 with total as 30 and status as pending",
        "remember a list called orders with o1 and o2",
        "remember how to find-big from limit: keep the orders where total is above limit",
        "find-big from 50",
    ])
    assert all(r.status is ResultStatus.SUCCESS for r in results)
    assert results[4].output == ["total: 75, status: active"]


def test_quoted_string_literal_parameter_used_in_body():
    """2. `find-status from "in progress"` — multi-word quoted-string literal
    bound to the param and compared inside the body."""
    session, results = run_lines([
        'remember an order called o1 with total as 75 and status as "in progress"',
        "remember an order called o2 with total as 30 and status as pending",
        "remember a list called orders with o1 and o2",
        "remember how to find-status from wanted: keep the orders where status is wanted",
        'find-status from "in progress"',
    ])
    assert all(r.status is ResultStatus.SUCCESS for r in results)
    assert results[4].output == ["total: 75, status: in progress"]


def test_float_literal_parameter():
    """3. `find-big from 3.14` — a float literal parses to NumberLiteral(3.14)
    and binds as a number."""
    ast = parse_line("find-big from 3.14", comps={"find-big"})
    assert isinstance(ast, CompositionCallNode)
    assert ast.arg == NumberLiteral(value=3.14)
    # And it executes: keep orders whose total exceeds 3.14 (both match).
    session, results = run_lines([
        "remember an order called o1 with total as 75 and status as active",
        "remember an order called o2 with total as 30 and status as pending",
        "remember a list called orders with o1 and o2",
        "remember how to find-big from limit: keep the orders where total is above limit",
        "find-big from 3.14",
    ])
    assert results[4].status is ResultStatus.SUCCESS
    assert results[4].output == ["total: 75, status: active", "total: 30, status: pending"]


def test_body_references_param_bound_to_literal_via_show():
    """14. Body that directly shows the literal-bound param."""
    session, results = run_lines([
        "remember how to echo from x: show x",
        "echo from 42",
    ])
    assert results[1].status is ResultStatus.SUCCESS
    assert results[1].output == ["42"]


# ---------------------------------------------------------------------------
# 4–7 — regressions: bare names + parameter/argument arity rules
# ---------------------------------------------------------------------------


def test_bare_name_parameter_still_works():
    """4. `find-big from orders` — bare-name argument, the v2d §96 path."""
    ast = parse_line("find-big from orders", comps={"find-big"})
    assert isinstance(ast, CompositionCallNode)
    assert ast.arg == "orders"  # a plain string, not an AST node
    session, results = run_lines([
        "remember an order called o1 with total as 75 and status as active",
        "remember an order called o2 with total as 30 and status as pending",
        "remember a list called orders with o1 and o2",
        "remember how to find-big from data: keep the data where total is above 50",
        "find-big from orders",
    ])
    assert results[4].status is ResultStatus.SUCCESS
    assert results[4].output == ["total: 75, status: active"]


def test_composition_without_parameter_still_works():
    """5. A parameter-less composition is still callable bare."""
    session, results = run_lines([
        "remember a list called nums with 1 and 2 and 3",
        "remember how to tally: count the nums",
        "tally",
    ])
    assert results[2].status is ResultStatus.SUCCESS
    assert results[2].output == ["3"]


def test_parameter_expected_but_no_argument_errors():
    """6. Composition declares a param; the call provides none."""
    session, results = run_lines([
        "remember how to find-big from data: keep the data where total is above 50",
        "find-big",
    ])
    assert results[1].status is ResultStatus.ERROR_SEMANTIC
    assert "expects an input" in results[1].message


def test_no_parameter_but_argument_supplied_errors():
    """7. Composition declares no param; the call supplies one."""
    session, results = run_lines([
        "remember a list called nums with 1 and 2 and 3",
        "remember how to tally: count the nums",
        "tally from 50",
    ])
    assert results[2].status is ResultStatus.ERROR_SEMANTIC
    assert "doesn't take an input" in results[2].message


# ---------------------------------------------------------------------------
# 8 — literal param in a value-position (capturing) composition call
# ---------------------------------------------------------------------------


def test_literal_param_in_value_position_call():
    """8. `remember ... from <comp> from 50` — captures the return value of
    a parameterized call whose argument is a literal (two `from` tokens)."""
    session, results = run_lines([
        "remember an order called o1 with total as 75 and status as active",
        "remember an order called o2 with total as 30 and status as pending",
        "remember a list called orders with o1 and o2",
        "remember how to find-big from limit: keep the orders where total is above limit",
        "remember the results called big from find-big from 50",
        "count big",
    ])
    assert results[4].status is ResultStatus.SUCCESS
    assert results[5].output == ["1"]
    assert len(session.symtab["big"].value) == 1
    assert session.symtab["big"].value[0]["total"] == 75


# ---------------------------------------------------------------------------
# 9–10 — canonical rendering of literal-param calls
# ---------------------------------------------------------------------------


def test_render_numeric_literal_parameter_call():
    """9. Numeric literal renders as the bare number."""
    node = CompositionCallNode(name="check-threshold", arg=NumberLiteral(value=50))
    assert render(node) == "check-threshold from 50"
    node_f = CompositionCallNode(name="check-threshold", arg=NumberLiteral(value=3.14))
    assert render(node_f) == "check-threshold from 3.14"


def test_render_quoted_string_literal_parameter_call():
    """10. Quoted-string literal ALWAYS renders with quotes so it round-trips
    back to a literal rather than a name reference."""
    node = CompositionCallNode(name="check-status", arg=QuotedString(content="in progress"))
    assert render(node) == 'check-status from "in progress"'
    # Even a single-word string keeps its quotes (round-trip integrity).
    node1 = CompositionCallNode(name="check-status", arg=QuotedString(content="active"))
    assert render(node1) == 'check-status from "active"'


def test_render_roundtrip_quoted_literal_stays_literal():
    """Re-parsing rendered output preserves the QuotedString (not a name)."""
    node = CompositionCallNode(name="check-status", arg=QuotedString(content="active"))
    reparsed = parse_line(render(node), comps={"check-status"})
    assert isinstance(reparsed, CompositionCallNode)
    assert reparsed.arg == QuotedString(content="active")


# ---------------------------------------------------------------------------
# 11–12 — rejection regressions: reserved words and end-of-line
# ---------------------------------------------------------------------------


def test_reserved_word_after_from_errors():
    """11. A reserved word is still rejected as an argument."""
    out = parse_line("find-big from filter", comps={"find-big"})
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_PARSE
    assert "reserved" in out.message


def test_end_of_line_after_from_errors():
    """12. `<comp> from` with nothing after it is still an error."""
    out = parse_line("find-big from", comps={"find-big"})
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_PARSE
    assert "expected a name" in out.message


# ---------------------------------------------------------------------------
# 13 — shadowing: literal param shadows a global, original restored after
# ---------------------------------------------------------------------------


def test_literal_param_shadows_global_and_restores():
    """13. A global named the same as the param is shadowed by the literal
    for the duration of the call, then restored."""
    session, results = run_lines([
        "remember a value called limit with 999",
        "remember an order called o1 with total as 75 and status as active",
        "remember an order called o2 with total as 30 and status as pending",
        "remember a list called orders with o1 and o2",
        "remember how to find-big from limit: keep the orders where total is above limit",
        "find-big from 50",
        "show limit",
    ])
    # The call used the literal 50 as the threshold (only o1 qualifies)...
    assert results[5].output == ["total: 75, status: active"]
    # ...and the global `limit` (999) is restored afterward.
    assert results[6].output == ["999"]
    assert session.symtab["limit"].value == 999


# ---------------------------------------------------------------------------
# 15 — nested composition call with a literal param
# ---------------------------------------------------------------------------


def test_nested_composition_call_with_literal_param():
    """15. A composition body that itself calls another composition with a
    literal argument."""
    session, results = run_lines([
        "remember an order called o1 with total as 75 and status as active",
        "remember an order called o2 with total as 30 and status as pending",
        "remember a list called orders with o1 and o2",
        "remember how to big-ones from threshold: keep the orders where total is above threshold",
        "remember how to standard: big-ones from 50",
        "standard",
    ])
    assert all(r.status is ResultStatus.SUCCESS for r in results)
    assert results[5].output == ["total: 75, status: active"]

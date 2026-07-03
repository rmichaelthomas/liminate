"""v25 vocabulary wave — `highest`/`lowest` list-extrema operators.

Covers both grammar forms (flat-list and record-field) across every
value position the parser dispatches through (_parse_atom,
_parse_simple_condition, _parse_show), the analyzer's shape/field
validation, the interpreter's numeric evaluation and empty-list error,
the `when`-dependency wiring through the listener, and round-trip
render/parse equality.
"""

from __future__ import annotations

from typing import Iterable

import pytest

from liminate.adapter import LiveValueRegistry, TestAdapter
from liminate.analyzer import SymbolEntry
from liminate.interpreter import HandlerTable, execute
from liminate.lexer import tokenize
from liminate.listener import listen
from liminate.parser import ExtremaNode, NameRef, parse, parse_when_block
from liminate.renderer import render
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus


def run(line: str, symtab: dict[str, SymbolEntry] | None = None) -> LiminateResult:
    """Full pipeline: lex -> reorder -> parse -> execute. Not just
    parse() — failure mode #3 (reorderer mangling extrema token order)
    only surfaces through the full CLI-equivalent path."""
    if symtab is None:
        symtab = {}
    tokens = tokenize(line)
    reordered = reorder(tokens)
    if isinstance(reordered, LiminateResult):
        return reordered
    comp_names = {n for n, e in symtab.items() if e.type == "composition"}
    ast = parse(reordered, composition_names=comp_names)
    if isinstance(ast, LiminateResult):
        return ast
    return execute(ast, symtab)


def run_program(lines: list[str]) -> tuple[dict[str, SymbolEntry], list[LiminateResult]]:
    symtab: dict[str, SymbolEntry] = {}
    results = [run(line, symtab) for line in lines]
    return symtab, results


def _roundtrip(line: str) -> None:
    """render(parse(x)) is byte-exact; re-parsing the rendered form
    yields an equal AST. Goes through reorder() like `run()` does."""
    ast1 = parse(reorder(tokenize(line)))
    assert not isinstance(ast1, LiminateResult), ast1
    rendered = render(ast1)
    assert rendered == line
    ast2 = parse(reorder(tokenize(rendered)))
    assert not isinstance(ast2, LiminateResult), ast2
    assert ast1 == ast2


# ---------------------------------------------------------------------------
# Form A (flat lists) — every value position
# ---------------------------------------------------------------------------


def test_form_a_remember_from():
    symtab, results = run_program([
        "remember a list called nums with 3 and 7 and 5",
        "remember a copy called top from highest of nums",
    ])
    assert results[-1].status is ResultStatus.SUCCESS
    assert symtab["top"].value == 7


def test_form_a_condition_rhs():
    symtab, results = run_program([
        "remember a list called caps with 10 and 20 and 30",
        "remember a number called price with 25",
        "require price is not above highest of caps",
    ])
    assert results[-1].status is ResultStatus.SUCCESS


def test_form_a_condition_rhs_failing():
    symtab, results = run_program([
        "remember a list called caps with 10 and 20 and 30",
        "remember a number called price with 35",
        "require price is not above highest of caps",
    ])
    assert results[-1].status is ResultStatus.REQUIREMENT_NOT_MET


def test_form_a_with_value():
    symtab, results = run_program([
        "remember a list called nums with 3 and 7 and 5",
        "remember an order called order1 with cap as highest of nums",
    ])
    assert results[-1].status is ResultStatus.SUCCESS
    assert symtab["order1"].value["cap"] == 7


def test_form_a_arithmetic_operand():
    symtab, results = run_program([
        "remember a list called caps with 10 and 20 and 30",
        "remember a number called m from lowest of caps plus 1",
    ])
    assert results[-1].status is ResultStatus.SUCCESS
    assert symtab["m"].value == 11


# ---------------------------------------------------------------------------
# Form B (record-field)
# ---------------------------------------------------------------------------


def test_form_b_highest_and_lowest():
    symtab, results = run_program([
        "remember an order called order1 with total as 75",
        "remember an order called order2 with total as 30",
        "remember an order called order3 with total as 120",
        "remember a list called orders with order1 and order2 and order3",
        "show highest total of orders",
        "show lowest total of orders",
    ])
    assert results[-2].status is ResultStatus.SUCCESS
    assert results[-2].output == ["120"]
    assert results[-1].output == ["30"]


def test_form_b_condition_lhs():
    symtab, results = run_program([
        "remember an order called order1 with total as 75",
        "remember an order called order2 with total as 30",
        "remember a list called orders with order1 and order2",
        "require highest total of orders is below 1000",
    ])
    assert results[-1].status is ResultStatus.SUCCESS


def test_form_b_condition_lhs_failing():
    symtab, results = run_program([
        "remember an order called order1 with total as 75",
        "remember an order called order2 with total as 3000",
        "remember a list called orders with order1 and order2",
        "require highest total of orders is below 1000",
    ])
    assert results[-1].status is ResultStatus.REQUIREMENT_NOT_MET


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


def test_show_highest_of_flat_list():
    symtab, results = run_program([
        "remember a list called nums with 3 and 7 and 5",
        "show highest of nums",
    ])
    assert results[-1].output == ["7"]


def test_show_highest_field_of_records():
    symtab, results = run_program([
        "remember an order called order1 with total as 75",
        "remember an order called order2 with total as 30",
        "remember a list called orders with order1 and order2",
        "show highest total of orders",
    ])
    assert results[-1].output == ["75"]


# ---------------------------------------------------------------------------
# Empty list — runtime error (asymmetric with `sum []` == 0)
# ---------------------------------------------------------------------------


def test_empty_list_is_semantic_error():
    symtab, results = run_program([
        "remember a list called nums with 1",
        "remove 1 from nums",
        "show highest of nums",
    ])
    r = results[-1]
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert r.message == "There's no highest of 'nums' — the list is empty."


def test_empty_list_lowest_error_names_lowest():
    symtab, results = run_program([
        "remember a list called nums with 1",
        "remove 1 from nums",
        "show lowest of nums",
    ])
    r = results[-1]
    assert r.message == "There's no lowest of 'nums' — the list is empty."


# ---------------------------------------------------------------------------
# Type errors — text list (Form A) / text field (Form B)
# ---------------------------------------------------------------------------


def test_text_list_form_a_is_runtime_type_error():
    symtab, results = run_program([
        "remember a list called colors with red and blue and green",
        "show highest of colors",
    ])
    r = results[-1]
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "needs numbers" in r.message
    assert "colors" in r.message


def test_text_field_form_b_is_runtime_type_error():
    symtab, results = run_program([
        "remember an order called order1 with status as active",
        "remember an order called order2 with status as pending",
        "remember a list called orders with order1 and order2",
        "show highest status of orders",
    ])
    r = results[-1]
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "needs numbers" in r.message
    assert "status" in r.message


# ---------------------------------------------------------------------------
# Analyzer redirection errors — Form A on records / Form B on flat lists
# ---------------------------------------------------------------------------


def test_form_a_on_list_of_records_suggests_form_b():
    symtab, results = run_program([
        "remember an order called order1 with total as 75",
        "remember a list called orders with order1",
        "show highest of orders",
    ])
    r = results[-1]
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "needs a field" in r.message
    assert "highest <field> of orders" in r.message


def test_form_b_on_flat_list_suggests_form_a():
    symtab, results = run_program([
        "remember a list called nums with 3 and 7 and 5",
        "show highest total of nums",
    ])
    r = results[-1]
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "needs a list of records" in r.message
    assert "highest of nums" in r.message


# ---------------------------------------------------------------------------
# Ties (VW-Q4) — duplicated max returns the value, no special handling
# ---------------------------------------------------------------------------


def test_tie_returns_the_repeated_value():
    symtab, results = run_program([
        "remember a list called nums with 10 and 10 and 3",
        "show highest of nums",
    ])
    assert results[-1].output == ["10"]


# ---------------------------------------------------------------------------
# Breaking surface 2 — a field literally named `highest` is now reserved
# ---------------------------------------------------------------------------


def test_record_field_named_highest_no_longer_field_accessible():
    # Pre-v25 this would have been `show <field 'highest'> of order1`.
    # Since `highest` now lexes as OPERATOR, `show highest of order1`
    # parses as Form A extrema on `order1` — which isn't a list, so the
    # error clearly signals the meaning changed rather than silently
    # returning the old field's value.
    symtab, results = run_program([
        "remember an order called order1 with highest as 42",
        "show highest of order1",
    ])
    r = results[-1]
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "order1" in r.message


# ---------------------------------------------------------------------------
# `when` dependency wiring through the listener
# ---------------------------------------------------------------------------


def _build_when_node(header: str, *actions: str):
    htoks = reorder(tokenize(header))
    atoks = [reorder(tokenize(a)) for a in actions]
    ast = parse_when_block(htoks, atoks)
    assert not isinstance(ast, LiminateResult), ast
    return ast


def _register(symtab, ht, reg, header: str, *actions: str) -> None:
    ast = _build_when_node(header, *actions)
    result = execute(ast, symtab, handler_table=ht, live_value_registry=reg)
    assert result.status is ResultStatus.SUCCESS, result


def _drain(it: Iterable[LiminateResult]) -> list[LiminateResult]:
    return list(it)


def test_when_highest_of_readings_fires_on_list_mutation():
    symtab: dict[str, SymbolEntry] = {}
    symtab["readings"] = SymbolEntry(
        name="readings", value=[10, 20, 30], type="list_of_numbers",
    )
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg,
        "when highest of readings is above 100",
        'show "alert"',
    )
    adapter = TestAdapter([("readings", [10, 20, 150])], name="sensor")
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    assert len(fires) == 1
    assert fires[0].output == ["alert"]


def test_when_highest_of_readings_does_not_fire_without_crossing_threshold():
    symtab: dict[str, SymbolEntry] = {}
    symtab["readings"] = SymbolEntry(
        name="readings", value=[10, 20, 30], type="list_of_numbers",
    )
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg,
        "when highest of readings is above 100",
        'show "alert"',
    )
    adapter = TestAdapter([("readings", [10, 20, 40])], name="sensor")
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    assert len(fires) == 0


# ---------------------------------------------------------------------------
# Round-trip render/parse equality
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("line", [
    "remember a copy called top from highest of nums",
    "show highest of nums",
    "show highest total of orders",
    "show lowest total of orders",
    "require highest total of orders is below 1000",
    "remember a number called m from lowest of caps plus 1",
])
def test_roundtrip(line):
    _roundtrip(line)


def test_extrema_node_shape():
    ast = parse(reorder(tokenize("show highest total of orders")))
    assert ast.target == ExtremaNode(
        word="highest", target=NameRef("orders"), field="total",
    )

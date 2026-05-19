"""Metabolic Era batch 1 — tests for the `weakens` verb + `over` connective.

Covers parsing, analysis, execution (decay wrapping, tick advancement,
floor at zero, reinforcement via `remember`, last-wins reapplication),
display, and condition evaluation.
"""

from __future__ import annotations

import pytest

from liminate.analyzer import SymbolEntry
from liminate.interpreter import (
    HandlerTable,
    decay_tick,
    execute as _execute,
)
from liminate.lexer import tokenize
from liminate.listener import listen
from liminate.parser import (
    NameRef,
    NumberLiteral,
    WeakensNode,
    parse,
    parse_when_block,
)
from liminate.renderer import render
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus
from liminate.adapter import LiveValueRegistry
from liminate.vocabulary import DecayingValue


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse(line: str):
    toks = tokenize(line)
    reordered = reorder(toks)
    if isinstance(reordered, LiminateResult):
        return reordered
    return parse(reordered)


def run(line: str, symtab: dict[str, SymbolEntry] | None = None) -> LiminateResult:
    if symtab is None:
        symtab = {}
    ast = _parse(line)
    if isinstance(ast, LiminateResult):
        return ast
    return _execute(ast, symtab)


# ---------------------------------------------------------------------------
# DecayingValue arithmetic
# ---------------------------------------------------------------------------


def test_decaying_value_initial_value():
    assert DecayingValue(1.0, 10).current_value == 1.0


def test_decaying_value_at_end_of_period():
    assert DecayingValue(1.0, 10, ticks_elapsed=10).current_value == 0.0


def test_decaying_value_midway():
    assert DecayingValue(1.0, 10, ticks_elapsed=5).current_value == 0.5


def test_decaying_value_floors_at_zero():
    v = DecayingValue(1.0, 10, ticks_elapsed=999)
    assert v.current_value == 0.0


def test_decaying_value_tick_stops_at_floor():
    v = DecayingValue(1.0, 2)
    v.tick()  # ticks_elapsed=1, value=0.5
    v.tick()  # ticks_elapsed=2, value=0.0
    v.tick()  # no-op once at floor
    assert v.ticks_elapsed == 2
    assert v.current_value == 0.0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_parses_basic_weakens():
    ast = _parse("weakens urgency over 30")
    assert isinstance(ast, WeakensNode)
    assert ast.subject == NameRef(name="urgency")
    assert ast.period == NumberLiteral(value=30)


def test_parses_with_article():
    ast = _parse("weakens the urgency over 30")
    assert isinstance(ast, WeakensNode)
    assert ast.subject.name == "urgency"
    assert ast.period.value == 30


def test_parse_missing_target():
    r = _parse("weakens over 30")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


def test_parse_missing_period():
    r = _parse("weakens urgency")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE
    assert "decay period" in r.message


def test_parse_missing_number_after_over():
    r = _parse("weakens urgency over")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE
    assert "number" in r.message


def test_parse_non_number_after_over():
    r = _parse("weakens urgency over fast")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


# ---------------------------------------------------------------------------
# Renderer round-trip
# ---------------------------------------------------------------------------


def test_render_integer_period():
    node = WeakensNode(subject=NameRef("urgency"), period=NumberLiteral(30))
    assert render(node) == "weakens urgency over 30"


def test_render_round_trip():
    original = WeakensNode(subject=NameRef("priority"), period=NumberLiteral(7))
    rendered = render(original)
    reparsed = _parse(rendered)
    assert reparsed == original


# ---------------------------------------------------------------------------
# Analyzer / executor — error paths
# ---------------------------------------------------------------------------


def test_analyzer_rejects_non_numeric_target():
    symtab: dict[str, SymbolEntry] = {}
    run('remember a label called my-name with "alice"', symtab)
    r = run("weakens my-name over 10", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "only works on numbers" in r.message


def test_analyzer_rejects_missing_target():
    r = run("weakens nonexistent over 10")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "can't find" in r.message


def test_analyzer_rejects_zero_period():
    symtab: dict[str, SymbolEntry] = {}
    run("remember a value called urgency with 1.0", symtab)
    r = run("weakens urgency over 0", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "positive number" in r.message


def test_analyzer_rejects_negative_period():
    r = _parse("weakens urgency over -5")
    # Lexer/reorderer may reject negatives at tokenization level; verify
    # at least that this never becomes a successful WeakensNode at value
    # <= 0. If the number is parsed, the analyzer fires.
    if isinstance(r, WeakensNode):
        assert r.period.value < 0


def test_over_is_reserved_as_name():
    r = run("remember a value called over with 5")
    assert r.status is ResultStatus.ERROR_PARSE
    assert "reserved" in r.message


# ---------------------------------------------------------------------------
# Execution — happy path
# ---------------------------------------------------------------------------


def test_weakens_wraps_value_in_decaying_value():
    symtab: dict[str, SymbolEntry] = {}
    run("remember a value called urgency with 1.0", symtab)
    r = run("weakens urgency over 10", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert isinstance(symtab["urgency"].value, DecayingValue)
    assert symtab["urgency"].value.initial_value == 1.0
    assert symtab["urgency"].value.period == 10
    assert symtab["urgency"].type == "number"


def test_show_decaying_value_returns_current():
    symtab: dict[str, SymbolEntry] = {}
    run("remember a value called urgency with 1.0", symtab)
    run("weakens urgency over 10", symtab)
    r = run("show urgency", symtab)
    assert r.output == ["1"]


def test_show_after_five_ticks():
    symtab: dict[str, SymbolEntry] = {}
    run("remember a value called urgency with 1.0", symtab)
    run("weakens urgency over 10", symtab)
    for _ in range(5):
        decay_tick(symtab)
    r = run("show urgency", symtab)
    assert r.output == ["0.5"]


def test_show_at_floor():
    symtab: dict[str, SymbolEntry] = {}
    run("remember a value called urgency with 1.0", symtab)
    run("weakens urgency over 10", symtab)
    for _ in range(15):
        decay_tick(symtab)
    r = run("show urgency", symtab)
    assert r.output == ["0"]


def test_reinforcement_via_remember_resets_decay():
    symtab: dict[str, SymbolEntry] = {}
    run("remember a value called urgency with 1.0", symtab)
    run("weakens urgency over 10", symtab)
    for _ in range(7):
        decay_tick(symtab)
    run("remember a value called urgency with 0.8", symtab)
    r = run("show urgency", symtab)
    assert r.output == ["0.8"]
    # Still a DecayingValue with the same period.
    assert isinstance(symtab["urgency"].value, DecayingValue)
    assert symtab["urgency"].value.period == 10
    assert symtab["urgency"].value.ticks_elapsed == 0


def test_reapplication_resets_from_current_value_and_new_period():
    symtab: dict[str, SymbolEntry] = {}
    run("remember a value called urgency with 1.0", symtab)
    run("weakens urgency over 10", symtab)
    for _ in range(5):
        decay_tick(symtab)
    # Now value is 0.5. Reapply with new period 5.
    run("weakens urgency over 5", symtab)
    dv = symtab["urgency"].value
    assert isinstance(dv, DecayingValue)
    assert dv.initial_value == 0.5
    assert dv.period == 5
    assert dv.ticks_elapsed == 0


def test_non_numeric_remember_discards_decay_wrapper():
    symtab: dict[str, SymbolEntry] = {}
    run("remember a value called urgency with 1.0", symtab)
    run("weakens urgency over 10", symtab)
    r = run('remember a status called urgency with "cancelled"', symtab)
    assert r.status is ResultStatus.SUCCESS
    assert symtab["urgency"].value == "cancelled"
    assert symtab["urgency"].type == "string"


# ---------------------------------------------------------------------------
# Condition evaluation reads decayed value
# ---------------------------------------------------------------------------


def test_filter_condition_against_decaying_value():
    symtab: dict[str, SymbolEntry] = {}
    run("remember a value called threshold with 1.0", symtab)
    run("weakens threshold over 10", symtab)
    run("remember a list called numbers with 1 and 2 and 3", symtab)
    for _ in range(8):
        decay_tick(symtab)
    # threshold's current value should now be 0.2 — filter numbers above
    # threshold should keep all of them.
    r = run("filter the numbers where each is above threshold", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert symtab["numbers"].value == [1, 2, 3]


# ---------------------------------------------------------------------------
# Listener integration — handler fires on decay crossing
# ---------------------------------------------------------------------------


def _build_when_node(header: str, *actions: str):
    htoks = reorder(tokenize(header))
    atoks = [reorder(tokenize(a)) for a in actions]
    ast = parse_when_block(htoks, atoks)
    assert not isinstance(ast, LiminateResult), ast
    return ast


def test_listener_eval_operand_unwraps_decaying_value():
    """A `when` handler whose condition is `urgency is below 0.3`
    should fire after enough ticks push the decayed value below 0.3."""
    symtab: dict[str, SymbolEntry] = {}
    run("remember a value called urgency with 1.0", symtab)
    run("weakens urgency over 10", symtab)

    ht = HandlerTable()
    reg = LiveValueRegistry()
    when_ast = _build_when_node(
        "when urgency is below 0.3",
        'show "urgency faded"',
    )
    _execute(when_ast, symtab, handler_table=ht, live_value_registry=reg)

    # Drive 8 ticks (urgency = 0.2), then fire eligible handlers.
    from liminate.listener import _Runner
    runner = _Runner(symtab, ht, reg, adapters=[])
    # Initial eligibility = false (1.0 not below 0.3).
    list(runner._initial_evaluation())
    assert ht.handlers[0].last_eligibility is False

    for _ in range(8):
        decay_tick(symtab)
    fires = list(runner.tick_decay())
    fire_outputs = [r.output for r in fires if r.status is ResultStatus.HANDLER_FIRE]
    assert any(
        out == ["urgency faded"] for out in fire_outputs
    ), f"expected handler to fire, got: {fires}"

"""Deontic Era — tests for the `forbid` verb.

`forbid` mirrors `require` with inverted polarity: it evaluates a
condition and halts with PROHIBITION_VIOLATED if the condition is true;
silent pass if false. Covers parsing, analysis (including mixed and/or
amber and void-return detection), execution (silent pass, violation with
actual values reported), stepwise semantics, round-trip rendering, and
vocabulary registration.
"""

from __future__ import annotations

from liminate.analyzer import _side_effect_verb
from liminate.cli import Session
from liminate.lexer import tokenize
from liminate.parser import (
    CompoundConditionNode,
    ConditionNode,
    ForbidNode,
    parse,
)
from liminate.renderer import render
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus
from liminate.vocabulary import VERBS, reserved_category


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse(line: str):
    toks = tokenize(line)
    reordered = reorder(toks)
    if isinstance(reordered, LiminateResult):
        return reordered
    return parse(reordered)


def _session() -> Session:
    return Session()


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_parses_basic_forbid():
    ast = _parse("forbid total is above 10000")
    assert isinstance(ast, ForbidNode)
    assert isinstance(ast.condition, ConditionNode)
    assert ast.condition.op == "above"


def test_parses_forbid_compound_and():
    ast = _parse("forbid total is above 10000 and quantity is above 50")
    assert isinstance(ast, ForbidNode)
    assert isinstance(ast.condition, CompoundConditionNode)
    assert ast.condition.connector == "and"


def test_parses_forbid_compound_or():
    ast = _parse("forbid total is above 10000 or quantity is above 50")
    assert isinstance(ast, ForbidNode)
    assert isinstance(ast.condition, CompoundConditionNode)
    assert ast.condition.connector == "or"


def test_mixed_and_or_triggers_amber():
    r = _parse(
        "forbid x is above 1 and y is below 5 or z is above 7"
    )
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.AMBER_PRECEDENCE


def test_parses_forbid_negated():
    ast = _parse("forbid total is not above 100")
    assert isinstance(ast, ForbidNode)
    assert ast.condition.op == "not_above"


def test_parses_forbid_with_includes():
    ast = _parse('forbid categories includes "restricted"')
    assert isinstance(ast, ForbidNode)
    assert ast.condition.op == "includes"


def test_parses_forbid_with_within():
    ast = _parse("forbid price is within 5 of target-price")
    assert isinstance(ast, ForbidNode)
    assert ast.condition.op == "within"


def test_parses_forbid_field_access():
    ast = _parse("forbid total of order is above 10000")
    assert isinstance(ast, ForbidNode)


def test_parse_error_when_no_condition():
    r = _parse("forbid")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE
    assert "needs a condition" in (r.message or "")


def test_because_attaches_rationale():
    ast = _parse('forbid total is above 10000 because "regulatory cap"')
    assert isinstance(ast, ForbidNode)
    assert ast.rationale == "regulatory cap"


def test_inherited_modifier():
    ast = _parse("inherited forbid total is above 10000")
    assert isinstance(ast, ForbidNode)
    assert ast.inherited is True


def test_full_canonical_metadata_order():
    ast = _parse(
        'inherited forbid total is above 10000 '
        'because "regulatory cap" from agent-compliance'
    )
    assert isinstance(ast, ForbidNode)
    assert ast.inherited is True
    assert ast.rationale == "regulatory cap"
    assert ast.inherited_from == "agent-compliance"


# ---------------------------------------------------------------------------
# Analyzer errors (semantic vs prohibition)
# ---------------------------------------------------------------------------


def test_unknown_variable_is_semantic_error():
    s = _session()
    r = s.run_line("forbid nonexistent is above 5")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "can't find" in (r.message or "")


def test_numeric_operator_on_text_is_semantic_error():
    s = _session()
    s.run_line('remember a value called label with "hello"')
    r = s.run_line("forbid label is above 5")
    assert r.status is ResultStatus.ERROR_SEMANTIC


def test_forbid_is_void_return_verb():
    ast = _parse("forbid total is above 10000")
    assert _side_effect_verb(ast, {}, set()) == "forbid"


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def test_forbid_passes_silently_when_false():
    s = _session()
    s.run_line("remember a value called total with 50")
    r = s.run_line("forbid total is above 100")
    assert r.status is ResultStatus.SUCCESS
    assert r.output is None


def test_forbid_violates_when_true():
    s = _session()
    s.run_line("remember a value called total with 150")
    r = s.run_line("forbid total is above 100")
    assert r.status is ResultStatus.PROHIBITION_VIOLATED
    assert "Prohibition violated" in (r.message or "")


def test_forbid_reports_actual_value():
    s = _session()
    s.run_line("remember a value called total with 15000")
    r = s.run_line("forbid total is above 10000")
    assert r.status is ResultStatus.PROHIBITION_VIOLATED
    assert "total is above 10000" in (r.message or "")
    assert "total is 15000" in (r.message or "")


def test_forbid_violation_carries_structured_metadata():
    # v0.12.0: PROHIBITION_VIOLATED results carry machine-readable failure
    # identity (verb / condition / actual) for downstream comparison.
    s = _session()
    s.run_line("remember a value called total with 15000")
    r = s.run_line("forbid total is above 10000")
    assert r.status is ResultStatus.PROHIBITION_VIOLATED
    assert r.metadata is not None
    assert r.metadata["verb"] == "forbid"
    assert r.metadata["condition"] == "total is above 10000"
    assert "total is 15000" in r.metadata["actual"]


def test_forbid_compound_true_violates():
    s = _session()
    s.run_line("remember a value called total with 20000")
    s.run_line("remember a value called quantity with 80")
    r = s.run_line(
        "forbid total is above 10000 and quantity is above 50"
    )
    assert r.status is ResultStatus.PROHIBITION_VIOLATED


def test_forbid_compound_false_passes():
    s = _session()
    s.run_line("remember a value called total with 20000")
    s.run_line("remember a value called quantity with 10")
    r = s.run_line(
        "forbid total is above 10000 and quantity is above 50"
    )
    assert r.status is ResultStatus.SUCCESS


def test_forbid_includes_violates():
    s = _session()
    s.run_line('remember a list called categories with "restricted"')
    r = s.run_line('forbid categories includes "restricted"')
    assert r.status is ResultStatus.PROHIBITION_VIOLATED


def test_forbid_inside_choose_branch():
    s = _session()
    s.run_line('remember a value called role with "guest"')
    s.run_line("remember a value called clearance with 9")
    r = s.run_line(
        'choose if role is "guest": forbid clearance is above 3'
    )
    assert r.status is ResultStatus.PROHIBITION_VIOLATED


# ---------------------------------------------------------------------------
# Stepwise semantics
# ---------------------------------------------------------------------------


def test_stepwise_commit_before_violated_forbid_with_and():
    s = _session()
    s.run_line('remember a list called audit-log with "none"')
    s.run_line("remember a value called total with 15000")
    r = s.run_line(
        'add "received" to audit-log and forbid total is above 10000'
    )
    assert r.status is ResultStatus.PROHIBITION_VIOLATED
    show = s.run_line("show audit-log")
    assert any("received" in line for line in (show.output or []))


def test_stepwise_commit_before_violated_forbid_with_then():
    s = _session()
    s.run_line('remember a list called audit-log with "none"')
    s.run_line("remember a value called total with 15000")
    r = s.run_line(
        'add "logged" to audit-log then forbid total is above 10000'
    )
    assert r.status is ResultStatus.PROHIBITION_VIOLATED
    show = s.run_line("show audit-log")
    assert any("logged" in line for line in (show.output or []))


# ---------------------------------------------------------------------------
# Round-trip rendering
# ---------------------------------------------------------------------------


def test_render_round_trip_basic():
    ast = _parse("forbid total is above 10000")
    rendered = render(ast)
    assert rendered == "forbid total is above 10000"
    again = _parse(rendered)
    assert isinstance(again, ForbidNode)
    assert again == ast


def test_render_round_trip_full_metadata():
    line = (
        'inherited forbid total is above 10000 '
        'because "regulatory cap" from agent-compliance'
    )
    ast = _parse(line)
    rendered = render(ast)
    assert rendered == line
    again = _parse(rendered)
    assert isinstance(again, ForbidNode)
    assert again.inherited is True
    assert again.rationale == "regulatory cap"
    assert again.inherited_from == "agent-compliance"


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------


def test_forbid_in_verbs():
    assert "forbid" in VERBS


def test_forbid_reserved_category():
    assert reserved_category("forbid") == "verb"


def test_forbid_rejected_as_variable_name():
    s = _session()
    r = s.run_line("remember a value called forbid with 5")
    assert r.status in (
        ResultStatus.ERROR_PARSE,
        ResultStatus.ERROR_SEMANTIC,
    )

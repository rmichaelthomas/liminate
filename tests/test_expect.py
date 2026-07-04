"""Epistemic Era batch 3 — tests for the `expect` verb.

Covers parsing, analysis (including mixed and/or amber), execution
(silent pass, divergence output on fail — never halting), behavior
inside choose / each / compositions / when action blocks, and
interactions with `require` and `assign`.
"""

from __future__ import annotations

from liminate.cli import Session
from liminate.lexer import tokenize
from liminate.parser import (
    CompoundConditionNode,
    ConditionNode,
    ExpectNode,
    parse,
)
from liminate.renderer import render
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus


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


def _output_str(r) -> str:
    return "\n".join(r.output or [])


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_parses_basic_expect():
    ast = _parse("expect revenue is above 1000000")
    assert isinstance(ast, ExpectNode)
    assert isinstance(ast.condition, ConditionNode)
    assert ast.condition.op == "above"


def test_parses_expect_equality():
    ast = _parse('expect status is "approved"')
    assert isinstance(ast, ExpectNode)
    assert ast.condition.op == "is"


def test_parses_expect_includes():
    ast = _parse('expect roles includes "admin"')
    assert isinstance(ast, ExpectNode)
    assert ast.condition.op == "includes"


def test_parses_expect_negated_includes():
    ast = _parse('expect allergy-list not includes "penicillin"')
    assert isinstance(ast, ExpectNode)
    assert ast.condition.op == "not_includes"


def test_parses_expect_compound_and():
    ast = _parse("expect revenue is above 1000000 and margin is above 0.1")
    assert isinstance(ast, ExpectNode)
    assert isinstance(ast.condition, CompoundConditionNode)
    assert ast.condition.connector == "and"


def test_parse_error_no_condition():
    r = _parse("expect")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE
    assert "needs a condition" in (r.message or "")


def test_mixed_and_or_triggers_amber():
    r = _parse("expect x is above 1 and y is below 5 or z is 3")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.AMBER_PRECEDENCE


def test_render_round_trip_basic():
    ast = _parse("expect revenue is above 1000000")
    rendered = render(ast)
    assert rendered == "expect revenue is above 1000000"
    again = _parse(rendered)
    assert isinstance(again, ExpectNode)


# ---------------------------------------------------------------------------
# Execution — met expectations are silent and SUCCESS
# ---------------------------------------------------------------------------


def test_expect_met_is_silent():
    s = _session()
    s.run_line("remember a value called revenue with 1500000")
    r = s.run_line("expect revenue is above 1000000")
    assert r.status is ResultStatus.SUCCESS
    assert not (r.output or [])


def test_expect_met_equality():
    s = _session()
    s.run_line('remember a value called status with "approved"')
    r = s.run_line('expect status is "approved"')
    assert r.status is ResultStatus.SUCCESS
    assert not (r.output or [])


def test_expect_met_includes():
    s = _session()
    s.run_line('remember a list called roles with "admin"')
    r = s.run_line('expect roles includes "admin"')
    assert r.status is ResultStatus.SUCCESS
    assert not (r.output or [])


def test_expect_met_negated():
    s = _session()
    s.run_line('remember a list called allergy-list with "sulfa"')
    r = s.run_line('expect allergy-list not includes "penicillin"')
    assert r.status is ResultStatus.SUCCESS


def test_expect_met_compound_and():
    s = _session()
    s.run_line("remember a value called revenue with 1500000")
    s.run_line("remember a value called margin with 0.2")
    r = s.run_line(
        "expect revenue is above 1000000 and margin is above 0.1"
    )
    assert r.status is ResultStatus.SUCCESS


# ---------------------------------------------------------------------------
# Execution — diverged expectations emit output but stay SUCCESS
# ---------------------------------------------------------------------------


def test_expect_diverged_emits_output_and_succeeds():
    s = _session()
    s.run_line("remember a value called revenue with 750000")
    r = s.run_line("expect revenue is above 1000000")
    assert r.status is ResultStatus.SUCCESS
    text = _output_str(r)
    assert "Expectation not met" in text
    assert "revenue is above 1000000" in text
    assert "revenue is 750000" in text


def test_expect_includes_divergence():
    s = _session()
    s.run_line('remember a list called roles with "user"')
    r = s.run_line('expect roles includes "admin"')
    assert r.status is ResultStatus.SUCCESS
    assert "Expectation not met" in _output_str(r)


def test_expect_negated_divergence():
    s = _session()
    s.run_line('remember a list called allergy-list with "penicillin"')
    r = s.run_line('expect allergy-list not includes "penicillin"')
    assert r.status is ResultStatus.SUCCESS
    assert "Expectation not met" in _output_str(r)


def test_expect_compound_and_reports_first_failing_branch():
    s = _session()
    s.run_line("remember a value called revenue with 500")
    s.run_line('remember a value called status with "approved"')
    r = s.run_line(
        'expect revenue is above 1000 and status is "approved"'
    )
    assert r.status is ResultStatus.SUCCESS
    assert "revenue is 500" in _output_str(r)


# ---------------------------------------------------------------------------
# Analyzer errors
# ---------------------------------------------------------------------------


def test_unknown_variable_is_semantic_error():
    s = _session()
    r = s.run_line("expect nonexistent is above 5")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "can't find" in (r.message or "")


# ---------------------------------------------------------------------------
# Context tests
# ---------------------------------------------------------------------------


def test_expect_inside_choose_branch():
    s = _session()
    s.run_line('remember a value called mode with "strict"')
    s.run_line("remember a value called margin with 0.05")
    r = s.run_line(
        'choose if mode is "strict": expect margin is above 0.2'
    )
    assert r.status is ResultStatus.SUCCESS
    assert "Expectation not met" in _output_str(r)


def test_expect_inside_composition():
    s = _session()
    s.run_line("remember a value called revenue with 750000")
    s.run_line(
        "remember how to forecast-check: expect revenue is above 1000000"
    )
    r = s.run_line("forecast-check")
    assert r.status is ResultStatus.SUCCESS
    assert "Expectation not met" in _output_str(r)


# ---------------------------------------------------------------------------
# Integration with require and assign
# ---------------------------------------------------------------------------


def test_expect_diverges_require_passes_both_run():
    s = _session()
    s.run_line("remember a value called revenue with 750000")
    # First an expectation that diverges (informational).
    r1 = s.run_line("expect revenue is above 1000000")
    assert r1.status is ResultStatus.SUCCESS
    assert "Expectation not met" in _output_str(r1)
    # Then a stricter floor that passes.
    r2 = s.run_line("require revenue is above 500000")
    assert r2.status is ResultStatus.SUCCESS


def test_assign_then_expect_met():
    s = _session()
    s.run_line('assign task-1 to "compliance-team"')
    r = s.run_line('expect task-1 is "compliance-team"')
    assert r.status is ResultStatus.SUCCESS
    assert not (r.output or [])


# ---------------------------------------------------------------------------
# v28 — `unless` exception clauses
# ---------------------------------------------------------------------------


def test_parses_expect_with_unless():
    ast = _parse(
        "expect revenue is above 1000000 unless recession is equal to yes"
    )
    assert isinstance(ast, ExpectNode)
    assert ast.condition.op == "above"
    assert isinstance(ast.exception, ConditionNode)


def test_parses_expect_without_unless_has_no_exception():
    ast = _parse("expect revenue is above 1000000")
    assert isinstance(ast, ExpectNode)
    assert ast.exception is None


def test_parses_expect_unless_before_because():
    ast = _parse(
        'expect revenue is above 1000000 unless recession is equal to '
        'yes because "macro"'
    )
    assert isinstance(ast, ExpectNode)
    assert ast.exception is not None
    assert ast.rationale == "macro"


def test_expect_unless_render_round_trip():
    ast = _parse(
        "expect revenue is above 1000000 unless recession is equal to yes"
    )
    rendered = render(ast)
    assert rendered == (
        "expect revenue is above 1000000 unless recession is equal to yes"
    )
    again = _parse(rendered)
    assert isinstance(again, ExpectNode)
    assert again == ast


# Execution semantics: report divergence when NOT main AND NOT exception.


def test_expect_unless_main_holds_silent():
    s = _session()
    s.run_line("remember a value called revenue with 1500000")
    s.run_line('remember a value called recession with "no"')
    r = s.run_line(
        'expect revenue is above 1000000 unless recession is equal to "yes"'
    )
    assert r.status is ResultStatus.SUCCESS
    assert not (r.output or [])


def test_expect_unless_main_fails_exception_explains_silent():
    s = _session()
    s.run_line("remember a value called revenue with 500000")
    s.run_line('remember a value called recession with "yes"')
    r = s.run_line(
        'expect revenue is above 1000000 unless recession is equal to "yes"'
    )
    assert r.status is ResultStatus.SUCCESS
    assert not (r.output or [])


def test_expect_unless_main_fails_exception_false_reports():
    s = _session()
    s.run_line("remember a value called revenue with 500000")
    s.run_line('remember a value called recession with "no"')
    r = s.run_line(
        'expect revenue is above 1000000 unless recession is equal to "yes"'
    )
    assert r.status is ResultStatus.SUCCESS
    text = _output_str(r)
    assert "Expectation not met" in text
    assert "revenue is above 1000000" in text

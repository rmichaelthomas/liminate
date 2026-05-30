"""Normative Era batch 2 — tests for the `require` verb.

Covers parsing, analysis (including mixed and/or amber), execution
(silent pass, REQUIREMENT_NOT_MET on fail with actual values reported),
behavior inside choose / each / compositions / when action blocks, and
stepwise semantics for `then`-sequenced operations.
"""

from __future__ import annotations

from liminate.analyzer import SymbolEntry
from liminate.cli import Session
from liminate.interpreter import (
    HandlerTable,
    execute as _execute,
)
from liminate.lexer import tokenize
from liminate.parser import (
    CompoundConditionNode,
    ConditionNode,
    RequireNode,
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


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_parses_basic_require():
    ast = _parse("require amount is above 50000")
    assert isinstance(ast, RequireNode)
    assert isinstance(ast.condition, ConditionNode)
    assert ast.condition.op == "above"


def test_parses_require_equality():
    ast = _parse('require status is "approved"')
    assert isinstance(ast, RequireNode)
    assert ast.condition.op == "is"


def test_parses_require_with_includes():
    ast = _parse('require roles includes "admin"')
    assert isinstance(ast, RequireNode)
    assert ast.condition.op == "includes"


def test_parses_require_with_not_includes():
    ast = _parse('require allergies not includes "penicillin"')
    assert isinstance(ast, RequireNode)
    assert ast.condition.op == "not_includes"


def test_parses_require_compound_and():
    ast = _parse('require amount is above 1000 and status is "approved"')
    assert isinstance(ast, RequireNode)
    assert isinstance(ast.condition, CompoundConditionNode)
    assert ast.condition.connector == "and"


def test_parses_require_compound_or():
    ast = _parse('require amount is above 1000 or status is "override"')
    assert isinstance(ast, RequireNode)
    assert isinstance(ast.condition, CompoundConditionNode)
    assert ast.condition.connector == "or"


def test_parses_require_field_access():
    ast = _parse("require total of order1 is above 50")
    assert isinstance(ast, RequireNode)


def test_parse_error_when_no_condition():
    r = _parse("require")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE
    assert "needs a condition" in (r.message or "")


def test_mixed_and_or_triggers_amber():
    r = _parse(
        "require x is above 1 and y is below 5 or z is 3"
    )
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.AMBER_PRECEDENCE


def test_render_round_trip_basic():
    ast = _parse("require amount is above 50000")
    rendered = render(ast)
    assert rendered == "require amount is above 50000"
    again = _parse(rendered)
    assert isinstance(again, RequireNode)


def test_render_round_trip_compound():
    ast = _parse('require amount is above 1000 and status is "approved"')
    rendered = render(ast)
    assert "require" in rendered and "and" in rendered
    again = _parse(rendered)
    assert isinstance(again, RequireNode)


# ---------------------------------------------------------------------------
# Execution — happy paths
# ---------------------------------------------------------------------------


def test_require_passes_silently():
    s = _session()
    s.run_line("remember a value called amount with 75000")
    r = s.run_line("require amount is above 50000")
    assert r.status is ResultStatus.SUCCESS
    assert r.output is None


def test_require_passes_on_equality():
    s = _session()
    s.run_line('remember a value called status with "approved"')
    r = s.run_line('require status is "approved"')
    assert r.status is ResultStatus.SUCCESS


def test_require_passes_on_includes():
    s = _session()
    s.run_line('remember a list called roles with "admin" and "user"')
    r = s.run_line('require roles includes "admin"')
    assert r.status is ResultStatus.SUCCESS


def test_require_passes_on_negated_includes():
    s = _session()
    s.run_line('remember a list called allergy-list with "sulfa"')
    r = s.run_line('require allergy-list not includes "penicillin"')
    assert r.status is ResultStatus.SUCCESS


def test_require_passes_compound_and():
    s = _session()
    s.run_line("remember a value called amount with 5000")
    s.run_line('remember a value called status with "approved"')
    r = s.run_line(
        'require amount is above 1000 and status is "approved"'
    )
    assert r.status is ResultStatus.SUCCESS


def test_require_passes_compound_or_one_true():
    s = _session()
    s.run_line("remember a value called amount with 500")
    s.run_line('remember a value called status with "override"')
    r = s.run_line(
        'require amount is above 1000 or status is "override"'
    )
    assert r.status is ResultStatus.SUCCESS


# ---------------------------------------------------------------------------
# Execution — failure paths
# ---------------------------------------------------------------------------


def test_require_fails_with_message_and_actual():
    s = _session()
    s.run_line("remember a value called amount with 30000")
    r = s.run_line("require amount is above 50000")
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET
    assert "Requirement not met" in (r.message or "")
    assert "amount is above 50000" in (r.message or "")
    assert "amount is 30000" in (r.message or "")


def test_require_failure_carries_structured_metadata():
    # v0.12.0: REQUIREMENT_NOT_MET results carry machine-readable failure
    # identity (verb / condition / actual) for downstream comparison.
    s = _session()
    s.run_line("remember a value called amount with 30000")
    r = s.run_line("require amount is above 50000")
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET
    assert r.metadata is not None
    assert r.metadata["verb"] == "require"
    assert r.metadata["condition"] == "amount is above 50000"
    assert "amount is 30000" in r.metadata["actual"]


def test_require_includes_fails():
    s = _session()
    s.run_line('remember a list called roles with "user"')
    r = s.run_line('require roles includes "admin"')
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET


def test_require_negated_includes_fails():
    s = _session()
    s.run_line('remember a list called allergy-list with "penicillin"')
    r = s.run_line('require allergy-list not includes "penicillin"')
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET


def test_require_compound_and_reports_first_failing_branch():
    s = _session()
    s.run_line("remember a value called amount with 500")
    s.run_line('remember a value called status with "approved"')
    # First sub-condition fails (amount=500, need >1000).
    r = s.run_line(
        'require amount is above 1000 and status is "approved"'
    )
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET
    assert "amount is 500" in (r.message or "")


# ---------------------------------------------------------------------------
# Analyzer errors (semantic vs requirement)
# ---------------------------------------------------------------------------


def test_unknown_variable_is_semantic_error_not_requirement():
    s = _session()
    r = s.run_line("require nonexistent is above 5")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "can't find" in (r.message or "")


# ---------------------------------------------------------------------------
# Inside other constructs
# ---------------------------------------------------------------------------


def test_require_inside_choose_branch_pass():
    s = _session()
    s.run_line('remember a value called role with "admin"')
    s.run_line("remember a value called clearance with 5")
    r = s.run_line(
        'choose if role is "admin": require clearance is above 3'
    )
    assert r.status is ResultStatus.SUCCESS


def test_require_inside_choose_branch_fail():
    s = _session()
    s.run_line('remember a value called role with "admin"')
    s.run_line("remember a value called clearance with 1")
    r = s.run_line(
        'choose if role is "admin": require clearance is above 3'
    )
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET


def test_require_inside_composition_call():
    s = _session()
    s.run_line("remember a value called balance with 100")
    s.run_line("remember how to check-balance: require balance is above 0")
    r = s.run_line("check-balance")
    assert r.status is ResultStatus.SUCCESS


def test_require_inside_composition_call_fail():
    s = _session()
    s.run_line("remember a value called balance with 0")
    s.run_line("remember how to check-balance: require balance is above 0")
    r = s.run_line("check-balance")
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET


# ---------------------------------------------------------------------------
# Stepwise semantics with `then`
# ---------------------------------------------------------------------------


def test_stepwise_commit_before_failed_require():
    s = _session()
    s.run_line('remember a list called audit-log with "none"')
    s.run_line("remember a value called amount with 30000")
    r = s.run_line(
        'add "received" to audit-log then require amount is above 50000'
    )
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET
    # Prior op committed.
    show = s.run_line("show audit-log")
    assert any("received" in line for line in (show.output or []))

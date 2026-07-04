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


# ---------------------------------------------------------------------------
# v28 — `unless` exception clauses
# ---------------------------------------------------------------------------


def test_parses_require_with_unless():
    ast = _parse(
        "require amount is above 50000 unless waiver is equal to yes"
    )
    assert isinstance(ast, RequireNode)
    assert ast.condition.op == "above"
    assert isinstance(ast.exception, ConditionNode)
    assert ast.exception.op == "equal_to"


def test_parses_require_without_unless_has_no_exception():
    ast = _parse("require amount is above 50000")
    assert isinstance(ast, RequireNode)
    assert ast.exception is None


def test_parses_require_unless_compound_exception():
    ast = _parse(
        "require x is above 10 unless flag-a is equal to yes and "
        "flag-b is equal to yes"
    )
    assert isinstance(ast, RequireNode)
    assert isinstance(ast.exception, CompoundConditionNode)
    assert ast.exception.connector == "and"


def test_parses_require_unless_with_field_access():
    ast = _parse(
        "require total of order is above 100 unless status of order "
        "is equal to exempt"
    )
    assert isinstance(ast, RequireNode)
    assert ast.exception is not None


def test_parses_require_unless_before_because():
    ast = _parse(
        'require x is above 10 unless y is equal to yes because "policy"'
    )
    assert isinstance(ast, RequireNode)
    assert ast.exception is not None
    assert ast.rationale == "policy"


def test_parses_require_unless_full_canonical_order():
    ast = _parse(
        'starting "2025-01-01" inherited require x is above 10 unless '
        'y is equal to yes because "policy" from agent-a'
    )
    assert isinstance(ast, RequireNode)
    assert ast.starting_date == "2025-01-01"
    assert ast.inherited is True
    assert ast.exception is not None
    assert ast.rationale == "policy"
    assert ast.inherited_from == "agent-a"


def test_parse_error_unless_with_no_exception_condition():
    r = _parse("require amount is above 50000 unless")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE
    assert "unless" in (r.message or "")


def test_parse_error_double_unless():
    r = _parse(
        "require x is above 10 unless y is equal to yes unless "
        "z is equal to yes"
    )
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


def test_require_each_does_not_consume_unless():
    # `require each` returns before the `unless` consumption code —
    # a trailing `unless` is left in the stream and errors.
    r = _parse(
        "require each x in items x is above 5 unless y is equal to yes"
    )
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


def test_require_unless_exception_field_not_compared_via_equals_bypass():
    # Two nodes differing only in exception must NOT compare equal —
    # the exception is semantic content (compare=True), not inert metadata.
    a = _parse("require x is above 10 unless y is equal to yes")
    b = _parse("require x is above 10 unless z is equal to yes")
    assert a != b


def test_require_unless_mixed_and_or_in_exception_triggers_amber():
    r = _parse(
        "require x is above 10 unless flag-a is equal to yes and "
        "flag-b is equal to yes or flag-c is equal to yes"
    )
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.AMBER_PRECEDENCE


def test_require_unless_render_round_trip():
    ast = _parse("require x is above 10 unless y is equal to yes")
    rendered = render(ast)
    assert rendered == "require x is above 10 unless y is equal to yes"
    again = _parse(rendered)
    assert isinstance(again, RequireNode)
    assert again == ast


# Execution semantics: halt when NOT main AND NOT exception.


def test_require_unless_main_holds_exception_irrelevant():
    s = _session()
    s.run_line("remember a value called amount with 60000")
    s.run_line('remember a value called waiver with "no"')
    r = s.run_line(
        'require amount is above 50000 unless waiver is equal to "yes"'
    )
    assert r.status is ResultStatus.SUCCESS


def test_require_unless_main_fails_exception_excuses():
    s = _session()
    s.run_line("remember a value called amount with 30000")
    s.run_line('remember a value called waiver with "yes"')
    r = s.run_line(
        'require amount is above 50000 unless waiver is equal to "yes"'
    )
    assert r.status is ResultStatus.SUCCESS


def test_require_unless_main_fails_exception_also_fails():
    s = _session()
    s.run_line("remember a value called amount with 30000")
    s.run_line('remember a value called waiver with "no"')
    r = s.run_line(
        'require amount is above 50000 unless waiver is equal to "yes"'
    )
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET
    assert "amount is above 50000" in (r.message or "")

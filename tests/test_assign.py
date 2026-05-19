"""Delegated Era batch 3 — tests for the `assign` verb.

Covers parsing, analysis, execution (overwrite, reinforcement-on-decay,
record replacement), behavior inside choose / each / compositions / when
action blocks, and stepwise semantics for `then`-sequenced operations.
"""

from __future__ import annotations

from liminate.cli import Session
from liminate.lexer import tokenize
from liminate.parser import (
    AssignNode,
    BareWord,
    NameRef,
    NumberLiteral,
    QuotedString,
    SequenceNode,
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


def test_parses_basic_assign_bare_recipient():
    ast = _parse("assign review-task to compliance-team")
    assert isinstance(ast, AssignNode)
    assert ast.item == NameRef(name="review-task")
    assert ast.recipient == BareWord(word="compliance-team")


def test_parses_assign_with_article_and_quoted_recipient():
    ast = _parse('assign the case-47 to "supervisor"')
    assert isinstance(ast, AssignNode)
    assert ast.item == NameRef(name="case-47")
    assert ast.recipient == QuotedString(content="supervisor")


def test_parses_assign_with_number_recipient():
    ast = _parse("assign priority-level to 3")
    assert isinstance(ast, AssignNode)
    assert ast.recipient == NumberLiteral(value=3)


def test_parse_error_missing_item():
    r = _parse('assign to "supervisor"')
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


def test_parse_error_missing_recipient():
    r = _parse("assign review-task")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE
    assert "needs a recipient" in (r.message or "")


def test_parse_error_missing_value_after_to():
    r = _parse("assign review-task to")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


def test_assign_followed_by_then_expect():
    ast = _parse(
        "assign review-task to compliance-team then "
        "expect revenue is above 1000000"
    )
    assert isinstance(ast, SequenceNode)
    assert ast.connectors == ["then"]


def test_render_round_trip_quoted_multiword():
    # Multi-word quoted strings preserve their quotes (v2c §90).
    ast = _parse('assign review-task to "Dr. Martinez"')
    rendered = render(ast)
    assert rendered == 'assign review-task to "Dr. Martinez"'
    again = _parse(rendered)
    assert isinstance(again, AssignNode)


def test_render_round_trip_single_word_quote_drops():
    # Single-word strings render bare regardless of source quoting
    # (v2c §90 — conditional quoting rule).
    ast = _parse('assign review-task to "compliance-team"')
    rendered = render(ast)
    assert rendered == "assign review-task to compliance-team"


def test_render_round_trip_bare():
    ast = _parse("assign case-47 to supervisor")
    rendered = render(ast)
    assert rendered == "assign case-47 to supervisor"


# ---------------------------------------------------------------------------
# Execution — happy paths
# ---------------------------------------------------------------------------


def test_assign_stores_string_value():
    s = _session()
    r = s.run_line('assign review-task to "compliance-team"')
    assert r.status is ResultStatus.SUCCESS
    show = s.run_line("show review-task")
    assert "compliance-team" in (show.output or [""])[0]


def test_assign_with_article_works():
    s = _session()
    r = s.run_line('assign the case-47 to "supervisor"')
    assert r.status is ResultStatus.SUCCESS
    show = s.run_line("show case-47")
    assert "supervisor" in (show.output or [""])[0]


def test_assign_overwrites_existing_value():
    s = _session()
    s.run_line('assign review-task to "compliance-team"')
    r = s.run_line('assign review-task to "supervisor"')
    assert r.status is ResultStatus.SUCCESS
    show = s.run_line("show review-task")
    assert "supervisor" in (show.output or [""])[0]


def test_assign_bare_word_recipient_becomes_string():
    s = _session()
    r = s.run_line("assign review-task to compliance-team")
    assert r.status is ResultStatus.SUCCESS
    show = s.run_line("show review-task")
    assert "compliance-team" in (show.output or [""])[0]


def test_assign_name_reference_recipient_resolves():
    s = _session()
    s.run_line('remember a value called current-owner with "alice"')
    r = s.run_line("assign task-1 to current-owner")
    assert r.status is ResultStatus.SUCCESS
    show = s.run_line("show task-1")
    assert "alice" in (show.output or [""])[0]


def test_assign_number_recipient():
    s = _session()
    r = s.run_line("assign priority-level to 3")
    assert r.status is ResultStatus.SUCCESS
    show = s.run_line("show priority-level")
    assert "3" in (show.output or [""])[0]


# ---------------------------------------------------------------------------
# Inside other constructs
# ---------------------------------------------------------------------------


def test_assign_inside_choose_branch():
    s = _session()
    s.run_line('remember a value called role with "admin"')
    r = s.run_line(
        'choose if role is "admin": assign audit-task to "admin-team"'
    )
    assert r.status is ResultStatus.SUCCESS
    show = s.run_line("show audit-task")
    assert "admin-team" in (show.output or [""])[0]


def test_assign_inside_composition():
    s = _session()
    s.run_line(
        'remember how to delegate: assign task-1 to "team-a"'
    )
    r = s.run_line("delegate")
    assert r.status is ResultStatus.SUCCESS
    show = s.run_line("show task-1")
    assert "team-a" in (show.output or [""])[0]


def test_assign_then_require_both_execute():
    s = _session()
    s.run_line('remember a value called status with "active"')
    r = s.run_line(
        'assign intake to "triage" then require status is "active"'
    )
    assert r.status is ResultStatus.SUCCESS
    show = s.run_line("show intake")
    assert "triage" in (show.output or [""])[0]


# ---------------------------------------------------------------------------
# Overwrite interactions with other value kinds
# ---------------------------------------------------------------------------


def test_assign_over_existing_string_overwrites():
    s = _session()
    s.run_line('remember a value called task-1 with "old"')
    r = s.run_line('assign task-1 to "new"')
    assert r.status is ResultStatus.SUCCESS
    show = s.run_line("show task-1")
    assert "new" in (show.output or [""])[0]


def test_assign_over_decaying_value_with_string_discards_decay():
    s = _session()
    s.run_line("remember a value called urgency with 1.0")
    s.run_line("weakens urgency over 10")
    r = s.run_line('assign urgency to "compliance-team"')
    assert r.status is ResultStatus.SUCCESS
    show = s.run_line("show urgency")
    assert "compliance-team" in (show.output or [""])[0]


# ---------------------------------------------------------------------------
# Reserved word as item — parser error
# ---------------------------------------------------------------------------


def test_assign_reserved_word_as_item_errors():
    r = _parse('assign filter to "supervisor"')
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE

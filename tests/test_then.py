"""Normative Era batch 2 — tests for the `then` sequencing connective.

`then` produces the same SequenceNode shape as `and` between operations,
with the `connectors` metadata distinguishing the join words. Covers
parsing, error paths (dangling `then`, non-verb follower), rendering
round-trip, mixed `and`/`then` chains, and behavior inside `when` action
blocks / compositions.
"""

from __future__ import annotations

from liminate.cli import Session
from liminate.lexer import tokenize
from liminate.parser import (
    AddNode,
    RequireNode,
    SequenceNode,
    ShowNode,
    parse,
)
from liminate.renderer import render
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus


def _parse(line: str):
    toks = tokenize(line)
    reordered = reorder(toks)
    if isinstance(reordered, LiminateResult):
        return reordered
    return parse(reordered)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_basic_then_chain():
    ast = _parse('show x then show y')
    assert isinstance(ast, SequenceNode)
    assert len(ast.operations) == 2
    assert ast.connectors == ["then"]


def test_triple_chain_then():
    ast = _parse(
        'add "received" to log then '
        'require amount is above 0 then show log'
    )
    assert isinstance(ast, SequenceNode)
    assert len(ast.operations) == 3
    assert ast.connectors == ["then", "then"]
    assert isinstance(ast.operations[0], AddNode)
    assert isinstance(ast.operations[1], RequireNode)
    assert isinstance(ast.operations[2], ShowNode)


def test_mixed_and_then_chain():
    ast = _parse(
        'add x to y and show y then require z is above 5'
    )
    assert isinstance(ast, SequenceNode)
    assert ast.connectors == ["and", "then"]


def test_dangling_then_is_parse_error():
    r = _parse('add x to y then')
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE
    assert "verb after 'then'" in (r.message or "")


def test_then_followed_by_non_verb_is_parse_error():
    r = _parse('add x to y then 5')
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


# ---------------------------------------------------------------------------
# Renderer round-trip
# ---------------------------------------------------------------------------


def test_render_then_sequence_basic():
    ast = _parse('show x then show y')
    assert render(ast) == "show x then show y"


def test_render_mixed_and_then():
    ast = _parse('show x and show y then show z')
    assert render(ast) == "show x and show y then show z"


def test_render_round_trip_then_workflow():
    src = (
        'add "received" to audit-log then '
        'require amount is above 0 then show audit-log'
    )
    ast = _parse(src)
    rendered = render(ast)
    again = _parse(rendered)
    assert isinstance(again, SequenceNode)
    assert again.connectors == ["then", "then"]


# ---------------------------------------------------------------------------
# Backward compat — legacy SequenceNode without connectors
# ---------------------------------------------------------------------------


def test_legacy_sequence_node_renders_with_and():
    # A SequenceNode built without `connectors` (legacy callers) must
    # still render with `and` joins.
    legacy = SequenceNode(
        operations=[_parse('show x'), _parse('show y')],
    )
    assert legacy.connectors == []
    assert render(legacy) == "show x and show y"


def test_and_only_chain_records_and_connectors():
    ast = _parse('show x and show y and show z')
    assert isinstance(ast, SequenceNode)
    assert ast.connectors == ["and", "and"]


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def test_then_chain_executes_in_order():
    s = Session()
    s.run_line('remember a list called log with "start"')
    r = s.run_line(
        'add "received" to log then add "validated" to log'
    )
    assert r.status is ResultStatus.SUCCESS
    show = s.run_line('show log')
    out = show.output or []
    # All three items should appear in order.
    text = " | ".join(out)
    assert text.index("start") < text.index("received") < text.index("validated")


def test_then_workflow_with_require_passes():
    s = Session()
    s.run_line('remember a list called log with "init"')
    s.run_line('remember a value called amount with 5000')
    r = s.run_line(
        'add "received" to log then '
        'require amount is above 0 then '
        'add "validated" to log'
    )
    assert r.status is ResultStatus.SUCCESS


def test_then_inside_composition():
    s = Session()
    s.run_line('remember a list called log with "init"')
    s.run_line(
        'remember how to workflow: '
        'add "a" to log then add "b" to log'
    )
    r = s.run_line('workflow')
    assert r.status is ResultStatus.SUCCESS

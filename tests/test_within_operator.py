"""Tests for the `within` numeric-tolerance condition operator — issue #19.

`<field> is within <amount> of <target>` is true when
`|field - target| <= amount`. Before this, `within` was a reserved base
word with no base-language behavior — it only did anything inside the
session pack's `measure` verb. This promotes it to a real condition
operator usable everywhere a condition appears: `require`, `expect`,
`filter`/`keep ... where`, `choose if`, and `when`/`unless`.

The base reserved-word count is unchanged (54) — `within` was already a
counted connective; it just now means something on its own.
"""

import io

import pytest

from liminate.cli import Session, run_file
from liminate.lexer import tokenize
from liminate.parser import (
    BareWord,
    ConditionNode,
    FieldAccessNode,
    NumberLiteral,
    RequireNode,
    parse,
)
from liminate.renderer import render
from liminate.result import ResultStatus
from liminate.vocabulary import ALL_RESERVED, reserved_category


def _run(tmp_path, src):
    p = tmp_path / "p.limn"
    p.write_text(src, encoding="utf-8")
    out = io.StringIO()
    run_file(str(p), out=out, quiet=True)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Vocabulary — `within` stays a connective; count unchanged
# ---------------------------------------------------------------------------


def test_within_still_connective_and_count_unchanged():
    assert reserved_category("within") == "connective"
    assert "within" in ALL_RESERVED
    assert len(ALL_RESERVED) == 54


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_parse_within_basic():
    node = parse(tokenize("require amount is within 5 of target"))
    assert isinstance(node, RequireNode)
    cond = node.condition
    assert isinstance(cond, ConditionNode)
    assert cond.op == "within"
    assert cond.value == NumberLiteral(5)        # tolerance
    assert isinstance(cond.value2, BareWord)      # target (name)
    assert cond.value2.word == "target"


def test_parse_within_name_tolerance_and_field_access_target():
    # The `of` in `within tol of total of o1` must split as
    # (tolerance=tol)(target=total of o1) — the tolerance must NOT swallow
    # the structural `of` as a field access.
    node = parse(tokenize("require amount is within tol of total of o1"))
    cond = node.condition
    assert cond.op == "within"
    assert isinstance(cond.value, BareWord) and cond.value.word == "tol"
    assert isinstance(cond.value2, FieldAccessNode)
    assert cond.value2.field == "total"
    assert cond.value2.record_name == "o1"


def test_parse_within_missing_of_errors():
    result = parse(tokenize("require amount is within 5"))
    assert result.status is ResultStatus.ERROR_PARSE
    assert "within" in result.message


def test_parse_within_non_numeric_tolerance_errors():
    result = parse(tokenize('require amount is within "lots" of target'))
    assert result.status is ResultStatus.ERROR_PARSE


# ---------------------------------------------------------------------------
# Evaluation — boundary is inclusive (<=)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected_pass",
    [(10, True), (12, True), (8, True), (13, False), (7, False)],  # within 2 of 10
)
def test_within_require_boundary(tmp_path, value, expected_pass):
    src = (
        f"remember a number called x with {value}\n"
        "require x is within 2 of 10\n"
        'show "passed"\n'
    )
    out = _run(tmp_path, src)
    if expected_pass:
        assert "passed" in out
        assert "Requirement not met" not in out
    else:
        assert "Requirement not met" in out


def test_within_in_keep(tmp_path):
    src = (
        "remember a list called readings with 9 and 10 and 13 and 20\n"
        "keep the readings where each is within 2 of 10\n"
    )
    out = _run(tmp_path, src)
    assert out.strip().splitlines()[-1] == "9, 10"


def test_within_in_choose(tmp_path):
    src = (
        "remember a number called amount with 12\n"
        'choose if amount is within 5 of 10: show "close" otherwise show "far"\n'
    )
    out = _run(tmp_path, src)
    assert "close" in out and "far" not in out


def test_within_name_tolerance_and_field_target_executes(tmp_path):
    src = (
        "remember an order called o1 with total as 100\n"
        "remember a number called amount with 103\n"
        "remember a number called tol with 5\n"
        'choose if amount is within tol of total of o1: show "in" otherwise show "out"\n'
    )
    out = _run(tmp_path, src)
    assert "in" in out and "out" not in out


# ---------------------------------------------------------------------------
# Analyzer — operands must be numeric
# ---------------------------------------------------------------------------


def test_within_non_numeric_operand_is_semantic_error():
    s = Session()
    s.run_line('remember a string called label with "hi"')
    s.run_line("remember a number called t with 1")
    result = s.run_line("require label is within 2 of t")
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "within" in result.message


# ---------------------------------------------------------------------------
# Phase 2 — `when ... within` fires
# ---------------------------------------------------------------------------


def test_within_when_handler_fires(tmp_path):
    src = (
        "remember a number called reading with 48\n"
        "remember a number called target with 50\n"
        "when reading is within 3 of target\n"
        '  show "in band"\n'
        "  finish\n"
    )
    out = _run(tmp_path, src)
    assert "in band" in out


# ---------------------------------------------------------------------------
# Renderer round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "src",
    [
        "require amount is within 5 of target",
        "keep the readings where each is within 2 of 10",
        "filter the readings where each is within 2 of baseline",
        "require amount is within tol of total of o1",
    ],
)
def test_within_round_trips(src):
    node = parse(tokenize(src))
    assert not hasattr(node, "status"), getattr(node, "message", node)
    rendered = render(node)
    assert "is within" in rendered and " of " in rendered
    assert parse(tokenize(rendered)) == node


def test_within_compound_condition(tmp_path):
    src = (
        "remember a number called x with 11\n"
        'require x is within 2 of 10 and x is above 5\n'
        'show "ok"\n'
    )
    out = _run(tmp_path, src)
    assert "ok" in out and "Requirement not met" not in out

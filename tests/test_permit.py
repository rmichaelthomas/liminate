"""Deontic Era batch 2 — tests for the `permit` verb.

`permit` completes the deontic triangle (require/forbid/permit). Unlike
`require` (halts on false) and `forbid` (halts on true), `permit` follows
the `expect` pattern: it emits an informational output line when the
condition is true and passes silently when false. It NEVER halts and
always returns SUCCESS. Covers parsing, analysis, execution (emit on
match, silent on miss, never halts), independence from require/forbid,
round-trip rendering, and vocabulary registration.
"""

from __future__ import annotations

from liminate.analyzer import _side_effect_verb
from liminate.cli import Session
from liminate.parser import (
    CompoundConditionNode,
    ConditionNode,
    PermitNode,
    parse,
)
from liminate.renderer import render
from liminate.reorderer import reorder
from liminate.lexer import tokenize
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


def test_parses_basic_permit():
    ast = _parse("permit expenses is below 5000")
    assert isinstance(ast, PermitNode)
    assert isinstance(ast.condition, ConditionNode)
    assert ast.condition.op == "below"


def test_parses_permit_compound_and():
    ast = _parse('permit expenses is below 5000 and category is "travel"')
    assert isinstance(ast, PermitNode)
    assert isinstance(ast.condition, CompoundConditionNode)
    assert ast.condition.connector == "and"


def test_parses_permit_compound_or():
    ast = _parse('permit expenses is below 5000 or category is "travel"')
    assert isinstance(ast, PermitNode)
    assert isinstance(ast.condition, CompoundConditionNode)
    assert ast.condition.connector == "or"


def test_mixed_and_or_triggers_amber():
    r = _parse(
        "permit x is below 1 and y is above 5 or z is below 7"
    )
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.AMBER_PRECEDENCE


def test_parses_permit_negated():
    ast = _parse("permit total is not above 100")
    assert isinstance(ast, PermitNode)
    assert ast.condition.op == "not_above"


def test_parses_permit_with_includes():
    ast = _parse('permit categories includes "approved"')
    assert isinstance(ast, PermitNode)
    assert ast.condition.op == "includes"


def test_parses_permit_with_within():
    ast = _parse("permit price is within 10 of budget")
    assert isinstance(ast, PermitNode)
    assert ast.condition.op == "within"


def test_parses_permit_field_access():
    ast = _parse("permit total of order is below 5000")
    assert isinstance(ast, PermitNode)


def test_parse_error_when_no_condition():
    r = _parse("permit")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE
    assert "needs a condition" in (r.message or "")


def test_because_attaches_rationale():
    ast = _parse(
        'permit expenses is below 5000 because "pre-approved threshold"'
    )
    assert isinstance(ast, PermitNode)
    assert ast.rationale == "pre-approved threshold"


def test_inherited_modifier():
    ast = _parse("inherited permit expenses is below 5000")
    assert isinstance(ast, PermitNode)
    assert ast.inherited is True


def test_full_canonical_metadata_order():
    ast = _parse(
        'inherited permit expenses is below 5000 '
        'because "pre-approved threshold" from agent-compliance'
    )
    assert isinstance(ast, PermitNode)
    assert ast.inherited is True
    assert ast.rationale == "pre-approved threshold"
    assert ast.inherited_from == "agent-compliance"


# ---------------------------------------------------------------------------
# Semantic / analyzer
# ---------------------------------------------------------------------------


def test_unknown_variable_is_semantic_error():
    s = _session()
    r = s.run_line("permit nonexistent is below 5")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "can't find" in (r.message or "")


def test_numeric_operator_on_text_is_semantic_error():
    s = _session()
    s.run_line('remember a value called label with "hello"')
    r = s.run_line("permit label is below 5")
    assert r.status is ResultStatus.ERROR_SEMANTIC


def test_permit_is_void_return_verb():
    ast = _parse("permit expenses is below 5000")
    assert _side_effect_verb(ast, {}, set()) == "permit"


# ---------------------------------------------------------------------------
# Execution — the key behavioral difference: emit on true, never halt
# ---------------------------------------------------------------------------


def test_permit_emits_when_true():
    s = _session()
    s.run_line("remember a value called expenses with 3000")
    r = s.run_line("permit expenses is below 5000")
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["Permitted: expenses is below 5000. expenses is 3000."]


def test_permit_silent_when_false():
    s = _session()
    s.run_line("remember a value called expenses with 8000")
    r = s.run_line("permit expenses is below 5000")
    assert r.status is ResultStatus.SUCCESS
    assert r.output is None


def test_permit_never_halts():
    s = _session()
    s.run_line("remember a value called expenses with 3000")
    r = s.run_line("permit expenses is below 5000")
    assert r.status is ResultStatus.SUCCESS
    assert r.status is not ResultStatus.PROHIBITION_VIOLATED
    assert r.status is not ResultStatus.REQUIREMENT_NOT_MET


def test_permit_compound_true_emits():
    s = _session()
    s.run_line("remember a value called expenses with 3000")
    s.run_line('remember a value called category with "travel"')
    r = s.run_line(
        'permit expenses is below 5000 and category is "travel"'
    )
    assert r.status is ResultStatus.SUCCESS
    assert r.output is not None and len(r.output) == 1


def test_permit_compound_false_silent():
    s = _session()
    s.run_line("remember a value called expenses with 9000")
    s.run_line('remember a value called category with "travel"')
    r = s.run_line(
        'permit expenses is below 5000 and category is "travel"'
    )
    assert r.status is ResultStatus.SUCCESS
    assert r.output is None


# ---------------------------------------------------------------------------
# Sequence / independence from require + forbid
# ---------------------------------------------------------------------------


def test_permit_then_failing_require_emits_then_halts():
    s = _session()
    s.run_line("remember a value called expenses with 3000")
    s.run_line("remember a value called total with 10")
    r = s.run_line(
        "permit expenses is below 5000 and require total is above 100"
    )
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET
    assert any("Permitted" in line for line in (r.output or []))


def test_permit_then_firing_forbid_emits_then_halts():
    s = _session()
    s.run_line("remember a value called expenses with 3000")
    s.run_line("remember a value called total with 150")
    r = s.run_line(
        "permit expenses is below 5000 and forbid total is above 100"
    )
    assert r.status is ResultStatus.PROHIBITION_VIOLATED
    assert any("Permitted" in line for line in (r.output or []))


def test_passing_require_then_permit_succeeds_with_output():
    s = _session()
    s.run_line("remember a value called total with 200")
    s.run_line("remember a value called expenses with 3000")
    r = s.run_line(
        "require total is above 100 and permit expenses is below 5000"
    )
    assert r.status is ResultStatus.SUCCESS
    assert any("Permitted" in line for line in (r.output or []))


def test_permit_then_permit_both_emit():
    s = _session()
    s.run_line("remember a value called expenses with 3000")
    s.run_line("remember a value called headcount with 2")
    r = s.run_line(
        "permit expenses is below 5000 then permit headcount is below 5"
    )
    assert r.status is ResultStatus.SUCCESS
    assert len([l for l in (r.output or []) if "Permitted" in l]) == 2


def test_all_three_deontic_verbs_independent():
    s = _session()
    s.run_line("remember a value called total with 200")
    s.run_line("remember a value called restricted-count with 0")
    s.run_line("remember a value called expenses with 3000")
    # require passes (total > 100), forbid passes (restricted-count not
    # above 5), permit emits (expenses < 5000). Net: SUCCESS with one
    # Permitted line.
    r = s.run_line(
        "require total is above 100 and "
        "forbid restricted-count is above 5 and "
        "permit expenses is below 5000"
    )
    assert r.status is ResultStatus.SUCCESS
    assert any("Permitted" in line for line in (r.output or []))


# ---------------------------------------------------------------------------
# Round-trip rendering
# ---------------------------------------------------------------------------


def test_render_round_trip_basic():
    ast = _parse("permit expenses is below 5000")
    rendered = render(ast)
    assert rendered == "permit expenses is below 5000"
    again = _parse(rendered)
    assert isinstance(again, PermitNode)
    assert again == ast


def test_render_round_trip_full_metadata():
    line = (
        'inherited permit expenses is below 5000 '
        'because "pre-approved threshold" from agent-compliance'
    )
    ast = _parse(line)
    rendered = render(ast)
    assert rendered == line
    again = _parse(rendered)
    assert isinstance(again, PermitNode)
    assert again.inherited is True
    assert again.rationale == "pre-approved threshold"
    assert again.inherited_from == "agent-compliance"


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------


def test_permit_in_verbs():
    assert "permit" in VERBS


def test_permit_reserved_category():
    assert reserved_category("permit") == "verb"


def test_permit_rejected_as_variable_name():
    s = _session()
    r = s.run_line("remember a value called permit with 5")
    assert r.status in (
        ResultStatus.ERROR_PARSE,
        ResultStatus.ERROR_SEMANTIC,
    )


# ---------------------------------------------------------------------------
# v28 — `unless` exception clauses (narrowing)
# ---------------------------------------------------------------------------


def test_parses_permit_with_unless():
    ast = _parse(
        "permit expenses is below 5000 unless frozen is equal to yes"
    )
    assert isinstance(ast, PermitNode)
    assert ast.condition.op == "below"
    assert isinstance(ast.exception, ConditionNode)


def test_parses_permit_without_unless_has_no_exception():
    ast = _parse("permit expenses is below 5000")
    assert isinstance(ast, PermitNode)
    assert ast.exception is None


def test_parses_permit_unless_before_because():
    ast = _parse(
        'permit expenses is below 5000 unless frozen is equal to yes '
        'because "narrowed"'
    )
    assert isinstance(ast, PermitNode)
    assert ast.exception is not None
    assert ast.rationale == "narrowed"


def test_permit_unless_render_round_trip():
    ast = _parse(
        "permit expenses is below 5000 unless frozen is equal to yes"
    )
    rendered = render(ast)
    assert rendered == (
        "permit expenses is below 5000 unless frozen is equal to yes"
    )
    again = _parse(rendered)
    assert isinstance(again, PermitNode)
    assert again == ast


# Execution semantics: emit when main AND NOT exception (narrowing).


def test_permit_unless_main_true_exception_false_emits():
    s = _session()
    s.run_line("remember a value called expenses with 3000")
    s.run_line('remember a value called frozen with "no"')
    r = s.run_line(
        'permit expenses is below 5000 unless frozen is equal to "yes"'
    )
    assert r.status is ResultStatus.SUCCESS
    assert r.output is not None
    assert any("Permitted" in line for line in r.output)


def test_permit_unless_main_true_exception_true_suppresses():
    s = _session()
    s.run_line("remember a value called expenses with 3000")
    s.run_line('remember a value called frozen with "yes"')
    r = s.run_line(
        'permit expenses is below 5000 unless frozen is equal to "yes"'
    )
    assert r.status is ResultStatus.SUCCESS
    assert r.output is None


def test_permit_unless_main_false_silent_regardless_of_exception():
    s = _session()
    s.run_line("remember a value called expenses with 9000")
    s.run_line('remember a value called frozen with "yes"')
    r = s.run_line(
        'permit expenses is below 5000 unless frozen is equal to "yes"'
    )
    assert r.status is ResultStatus.SUCCESS
    assert r.output is None

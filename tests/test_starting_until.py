"""Temporal-Boundary Era — tests for the `starting` and `until` connectives.

`starting "<date>"` declares an effective date; `until "<date>"` declares a
sunset clause. Both are statement-initial modifiers (like `inherited`) that
attach quoted ISO 8601 date strings as inert AST metadata. They never affect
runtime — temporal evaluation is a product-layer concern (Receipts server).
Canonical order: `starting ... until ... inherited <verb> ... because "..."
from <agent>`. Co-occurrence allowed; canonical order enforced by grammar.
"""

from __future__ import annotations

from liminate.cli import Session
from liminate.lexer import tokenize
from liminate.parser import parse
from liminate.renderer import render
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus
from liminate.vocabulary import CONNECTIVES, reserved_category


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
# Parsing — `starting` only
# ---------------------------------------------------------------------------


def test_starting_with_require():
    ast = _parse('starting "2025-07-01" require expenses is below 5000')
    assert not isinstance(ast, LiminateResult)
    assert ast.starting_date == "2025-07-01"
    assert ast.until_date is None


def test_starting_with_forbid():
    ast = _parse('starting "2025-07-01" forbid expenses is above 10000')
    assert not isinstance(ast, LiminateResult)
    assert ast.starting_date == "2025-07-01"


def test_starting_with_permit():
    ast = _parse('starting "2025-07-01" permit expenses is below 5000')
    assert not isinstance(ast, LiminateResult)
    assert ast.starting_date == "2025-07-01"


def test_starting_with_remember():
    ast = _parse('starting "2025-07-01" remember a value called threshold with 5')
    assert not isinstance(ast, LiminateResult)
    assert ast.starting_date == "2025-07-01"


def test_starting_without_date_is_parse_error():
    r = _parse("starting require expenses is below 5000")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


def test_starting_bad_format_is_parse_error():
    r = _parse('starting "not-a-date" require expenses is below 5000')
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


def test_starting_bare_number_is_parse_error():
    r = _parse("starting 2025 require expenses is below 5000")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


# ---------------------------------------------------------------------------
# Parsing — `until` only
# ---------------------------------------------------------------------------


def test_until_with_require():
    ast = _parse('until "2025-12-31" require expenses is below 5000')
    assert not isinstance(ast, LiminateResult)
    assert ast.until_date == "2025-12-31"
    assert ast.starting_date is None


def test_until_without_date_is_parse_error():
    r = _parse("until require expenses is below 5000")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


def test_until_bad_format_is_parse_error():
    r = _parse('until "bad-format" require expenses is below 5000')
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


# ---------------------------------------------------------------------------
# Parsing — co-occurrence (DT-Q4)
# ---------------------------------------------------------------------------


def test_starting_and_until_co_occur():
    ast = _parse(
        'starting "2025-07-01" until "2025-12-31" '
        "require expenses is below 5000"
    )
    assert not isinstance(ast, LiminateResult)
    assert ast.starting_date == "2025-07-01"
    assert ast.until_date == "2025-12-31"


def test_reversed_order_until_before_starting_is_parse_error():
    # Canonical order is `starting` before `until`. A reversed order
    # consumes `until` only; the trailing `starting` is left in the
    # stream and errors on the verb.
    r = _parse(
        'until "2025-12-31" starting "2025-07-01" '
        "require expenses is below 5000"
    )
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE


# ---------------------------------------------------------------------------
# Parsing — combination with all metadata
# ---------------------------------------------------------------------------


def test_all_six_metadata_fields():
    ast = _parse(
        'starting "2025-07-01" until "2025-12-31" inherited '
        'require expenses is below 5000 because "cap" from agent-compliance'
    )
    assert not isinstance(ast, LiminateResult)
    assert ast.starting_date == "2025-07-01"
    assert ast.until_date == "2025-12-31"
    assert ast.inherited is True
    assert ast.rationale == "cap"
    assert ast.inherited_from == "agent-compliance"


def test_starting_inherited_because_from():
    ast = _parse(
        'starting "2025-07-01" inherited forbid headcount is above 50 '
        'because "sunset" from agent-hr'
    )
    assert not isinstance(ast, LiminateResult)
    assert ast.starting_date == "2025-07-01"
    assert ast.until_date is None
    assert ast.inherited is True
    assert ast.rationale == "sunset"
    assert ast.inherited_from == "agent-hr"


def test_until_with_because():
    ast = _parse(
        'until "2025-12-31" permit expenses is below 5000 '
        'because "temporary allowance"'
    )
    assert not isinstance(ast, LiminateResult)
    assert ast.until_date == "2025-12-31"
    assert ast.rationale == "temporary allowance"


# ---------------------------------------------------------------------------
# Parsing — no temporal markers (backward compat)
# ---------------------------------------------------------------------------


def test_no_temporal_markers_defaults_none():
    ast = _parse("require expenses is below 5000")
    assert not isinstance(ast, LiminateResult)
    assert ast.starting_date is None
    assert ast.until_date is None


# ---------------------------------------------------------------------------
# Runtime — inert metadata (does not affect execution)
# ---------------------------------------------------------------------------


def test_starting_does_not_affect_passing_require():
    s = _session()
    s.run_line("remember a value called expenses with 3000")
    r = s.run_line('starting "2025-07-01" require expenses is below 5000')
    assert r.status is ResultStatus.SUCCESS


def test_starting_does_not_prevent_requirement_enforcement():
    s = _session()
    s.run_line("remember a value called expenses with 8000")
    r = s.run_line('starting "2025-07-01" require expenses is below 5000')
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET


def test_until_does_not_prevent_prohibition_enforcement():
    s = _session()
    s.run_line("remember a value called expenses with 15000")
    r = s.run_line('until "2025-12-31" forbid expenses is above 10000')
    assert r.status is ResultStatus.PROHIBITION_VIOLATED


# ---------------------------------------------------------------------------
# Reorderer
# ---------------------------------------------------------------------------


def test_reorder_preserves_temporal_prefix_with_target_before_verb():
    ast = _parse(
        'starting "2025-07-01" the orders filter where total is above 50'
    )
    assert not isinstance(ast, LiminateResult)
    assert ast.starting_date == "2025-07-01"
    # The verb was reordered to canonical position; the date survived.
    assert render(ast).startswith('starting "2025-07-01" filter the orders')


def test_reorder_preserves_all_three_prefixes():
    ast = _parse(
        'starting "2025-07-01" until "2025-12-31" inherited '
        "the orders filter where total is above 50"
    )
    assert not isinstance(ast, LiminateResult)
    assert ast.starting_date == "2025-07-01"
    assert ast.until_date == "2025-12-31"
    assert ast.inherited is True


# ---------------------------------------------------------------------------
# Renderer round-trip
# ---------------------------------------------------------------------------


def _round_trip(line: str):
    ast = _parse(line)
    assert not isinstance(ast, LiminateResult), f"parse failed: {line}"
    rendered = render(ast)
    assert rendered == line, f"render mismatch:\n  in : {line}\n  out: {rendered}"
    again = _parse(rendered)
    assert not isinstance(again, LiminateResult)
    assert again == ast


def test_round_trip_starting_only():
    _round_trip('starting "2025-07-01" require expenses is below 5000')


def test_round_trip_until_only():
    _round_trip('until "2025-12-31" forbid expenses is above 10000')


def test_round_trip_both():
    _round_trip(
        'starting "2025-07-01" until "2025-12-31" '
        "require expenses is below 5000"
    )


def test_round_trip_full_canonical():
    _round_trip(
        'starting "2025-07-01" until "2025-12-31" inherited '
        'require expenses is below 5000 because "cap" from agent-compliance'
    )


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------


def test_starting_in_connectives():
    assert "starting" in CONNECTIVES


def test_until_in_connectives():
    assert "until" in CONNECTIVES


def test_starting_reserved_category():
    assert reserved_category("starting") == "connective"


def test_until_reserved_category():
    assert reserved_category("until") == "connective"


def test_temporal_words_rejected_as_variable_names():
    s = _session()
    r1 = s.run_line("remember a value called starting with 5")
    r2 = s.run_line("remember a value called until with 5")
    assert r1.status in (ResultStatus.ERROR_PARSE, ResultStatus.ERROR_SEMANTIC)
    assert r2.status in (ResultStatus.ERROR_PARSE, ResultStatus.ERROR_SEMANTIC)

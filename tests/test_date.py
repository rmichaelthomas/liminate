"""Calendar Era (v29) — dates as a first-class value type.

Covers the full pipeline for the new `date` scalar type: lexer
classification, parser literal + calendar validation, `starting`/`until`
bare-date support, interpreter storage/display/comparison/arithmetic/
tolerance, `today` injection, analyzer type-checking, and renderer
round-trips. Zero new reserved words — `TokenType.DATE` is a literal
type, accounted the same way as `TokenType.NUMBER`.
"""

from __future__ import annotations

from datetime import date

import pytest

from liminate.cli import Session
from liminate.lexer import tokenize
from liminate.parser import (
    DateLiteral,
    RememberListNode,
    RememberRecordNode,
    RememberValueNode,
    parse,
)
from liminate.renderer import render
from liminate.result import ResultStatus
from liminate.run import run
from liminate.vocabulary import ALL_RESERVED, TokenType


def run_lines(lines):
    session = Session()
    results = [session.run_line(line) for line in lines]
    return session, results


# ---------------------------------------------------------------------------
# 8a — Lexer
# ---------------------------------------------------------------------------


def test_lexer_classifies_bare_date():
    toks = tokenize("2025-07-01")
    assert len(toks) == 1
    assert toks[0].type is TokenType.DATE
    assert toks[0].value == "2025-07-01"


def test_lexer_accepts_shape_defers_content_validation():
    # The lexer only checks shape; 2025-13-01 lexes as DATE even though
    # month 13 isn't real — the parser rejects the content.
    toks = tokenize("2025-13-01")
    assert toks[0].type is TokenType.DATE


def test_lexer_quoted_date_stays_quoted_string():
    toks = tokenize('"2025-07-01"')
    assert toks[0].type is TokenType.QUOTED_STRING
    assert toks[0].value == "2025-07-01"


def test_lexer_plain_number_not_date():
    toks = tokenize("2025")
    assert toks[0].type is TokenType.NUMBER


def test_lexer_hyphenated_word_not_date():
    toks = tokenize("due-date")
    assert toks[0].type is TokenType.UNKNOWN


def test_lexer_extra_hyphens_not_date():
    toks = tokenize("2025-07-01-extra")
    assert toks[0].type is TokenType.UNKNOWN


def test_vocabulary_count_unaffected_by_date():
    # DATE is a literal type, not vocabulary — ALL_RESERVED is untouched.
    assert "DATE" not in ALL_RESERVED
    assert isinstance(len(ALL_RESERVED), int)  # sanity: no crash importing


# ---------------------------------------------------------------------------
# 8b — Parser: DateLiteral
# ---------------------------------------------------------------------------


def test_parse_remember_date_value():
    node = parse(tokenize("remember a date called due-date with 2025-07-01"))
    assert isinstance(node, RememberValueNode)
    assert isinstance(node.value, DateLiteral)
    assert node.value.value == date(2025, 7, 1)


def test_parse_remember_record_date_field():
    node = parse(
        tokenize("remember an order called o1 with filed-date as 2025-07-01")
    )
    assert isinstance(node, RememberRecordNode)
    field_name, field_value = node.fields[0]
    assert field_name == "filed-date"
    assert isinstance(field_value, DateLiteral)
    assert field_value.value == date(2025, 7, 1)


def test_parse_remember_list_of_dates():
    node = parse(
        tokenize(
            "remember a list called deadlines with 2025-07-01 and 2025-08-01"
        )
    )
    assert isinstance(node, RememberListNode)
    assert len(node.items) == 2
    assert all(isinstance(i, DateLiteral) for i in node.items)
    assert node.items[0].value == date(2025, 7, 1)
    assert node.items[1].value == date(2025, 8, 1)


def test_parse_invalid_calendar_date_february_30():
    result = parse(tokenize("remember a date called d with 2025-02-30"))
    assert result.status is ResultStatus.ERROR_PARSE
    assert "valid calendar date" in result.message


def test_parse_invalid_calendar_date_month_13():
    result = parse(tokenize("remember a date called d with 2025-13-01"))
    assert result.status is ResultStatus.ERROR_PARSE
    assert "valid calendar date" in result.message


# ---------------------------------------------------------------------------
# 8c — starting/until with bare dates
# ---------------------------------------------------------------------------


def test_starting_accepts_bare_date():
    node = parse(tokenize("starting 2025-07-01 require x is above 10"))
    assert not hasattr(node, "status"), getattr(node, "message", node)
    assert node.starting_date == "2025-07-01"


def test_until_accepts_bare_date():
    node = parse(tokenize("until 2025-12-31 forbid x is above 50"))
    assert not hasattr(node, "status"), getattr(node, "message", node)
    assert node.until_date == "2025-12-31"


def test_starting_and_until_both_bare_dates():
    node = parse(
        tokenize("starting 2025-07-01 until 2025-12-31 require x is above 10")
    )
    assert not hasattr(node, "status"), getattr(node, "message", node)
    assert node.starting_date == "2025-07-01"
    assert node.until_date == "2025-12-31"


def test_starting_still_accepts_quoted_date():
    node = parse(tokenize('starting "2025-07-01" require x is above 10'))
    assert not hasattr(node, "status"), getattr(node, "message", node)
    assert node.starting_date == "2025-07-01"


# ---------------------------------------------------------------------------
# 8d — Interpreter: storage and display
# ---------------------------------------------------------------------------


def test_date_storage_and_display():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "show d",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert session.symtab["d"].type == "date"
    assert session.symtab["d"].value == date(2025, 7, 1)
    assert results[-1].output == ["2025-07-01"]


def test_date_record_field_display():
    session, results = run_lines([
        "remember an order called o1 with filed-date as 2025-07-01",
        "show filed-date of o1",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["2025-07-01"]


# ---------------------------------------------------------------------------
# 8e — Interpreter: date comparison
# ---------------------------------------------------------------------------


def test_date_below_passes():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "require d is below 2025-12-31",
    ])
    assert results[-1].status is ResultStatus.SUCCESS, results[-1].message


def test_date_above_passes():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "require d is above 2025-01-01",
    ])
    assert results[-1].status is ResultStatus.SUCCESS, results[-1].message


def test_date_equal_to_passes():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "require d is equal to 2025-07-01",
    ])
    assert results[-1].status is ResultStatus.SUCCESS, results[-1].message


def test_date_forbid_triggers():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "forbid d is above 2025-06-30",
    ])
    assert results[-1].status is ResultStatus.PROHIBITION_VIOLATED


def test_date_vs_number_is_semantic_error():
    # Both operands individually pass _require_comparable (number, date
    # are each an accepted category); the mismatch is only caught by the
    # runtime guard in _apply_op, which interpreter.py surfaces as
    # ERROR_SEMANTIC (this codebase's convention for _RuntimeError —
    # see the divide-by-zero test in test_arithmetic.py).
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "require d is above 50",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "compare a date" in results[-1].message


def test_date_vs_quoted_string_is_semantic_error():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        'require d is above "2025-01-01"',
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC


# ---------------------------------------------------------------------------
# 8f — Interpreter: date lists
# ---------------------------------------------------------------------------


def test_homogeneous_date_list_type():
    session, results = run_lines([
        "remember a list called deadlines with 2025-07-01 and 2025-08-01",
    ])
    assert results[-1].status is ResultStatus.SUCCESS, results[-1].message
    assert session.symtab["deadlines"].type == "list_of_dates"


def test_mixed_date_and_number_list_is_semantic_error():
    session, results = run_lines([
        "remember a list called mixed with 2025-07-01 and 5",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC


def test_sort_records_by_date_field():
    session, results = run_lines([
        "remember an order called o1 with filed-date as 2025-08-01",
        "remember an order called o2 with filed-date as 2025-06-01",
        "remember an order called o3 with filed-date as 2025-07-01",
        "remember a list called orders with o1 and o2 and o3",
        "sort the orders by filed-date",
        "each the orders show filed-date",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["2025-06-01", "2025-07-01", "2025-08-01"]


def test_highest_date_field():
    session, results = run_lines([
        "remember an order called o1 with filed-date as 2025-08-01",
        "remember an order called o2 with filed-date as 2025-06-01",
        "remember a list called orders with o1 and o2",
        "remember a date called latest from highest filed-date of orders",
        "show latest",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["2025-08-01"]


def test_lowest_date_field():
    session, results = run_lines([
        "remember an order called o1 with filed-date as 2025-08-01",
        "remember an order called o2 with filed-date as 2025-06-01",
        "remember a list called orders with o1 and o2",
        "remember a date called earliest from lowest filed-date of orders",
        "show earliest",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["2025-06-01"]


def test_date_list_includes():
    session, results = run_lines([
        "remember a list called deadlines with 2025-07-01 and 2025-08-01",
        "require deadlines includes 2025-07-01",
    ])
    assert results[-1].status is ResultStatus.SUCCESS, results[-1].message


def test_add_date_to_date_list():
    session, results = run_lines([
        "remember a list called deadlines with 2025-07-01 and 2025-08-01",
        "add 2025-10-01 to deadlines",
    ])
    assert results[-1].status is ResultStatus.SUCCESS, results[-1].message
    assert session.symtab["deadlines"].value == [
        date(2025, 7, 1), date(2025, 8, 1), date(2025, 10, 1),
    ]


# ---------------------------------------------------------------------------
# 8g — Interpreter: date arithmetic
# ---------------------------------------------------------------------------


def test_date_plus_number():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "remember a date called later from d plus 30",
        "show later",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["2025-07-31"]


def test_date_minus_number():
    session, results = run_lines([
        "remember a date called d with 2025-07-31",
        "remember a date called earlier from d minus 30",
        "show earlier",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["2025-07-01"]


def test_date_minus_date_yields_day_count():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "remember a value called gap from d minus 2025-01-01",
        "show gap",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["181"]


def test_date_plus_date_is_semantic_error():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "remember a date called d2 with 2025-01-01",
        "remember a value called bad from d plus d2",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "can't add two dates" in results[-1].message


def test_date_multiplied_by_is_semantic_error():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "remember a value called bad from d multiplied by 2",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "multiplied or divided" in results[-1].message


def test_date_plus_fractional_day_is_semantic_error():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "remember a value called bad from d plus 30.5",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "whole" in results[-1].message


def test_number_minus_date_is_semantic_error():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "remember a value called bad from 5 minus d",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC


def test_remember_date_from_field_plus_number():
    session, results = run_lines([
        "remember an order called o1 with filing-date as 2025-07-01",
        "remember a date called deadline from filing-date of o1 plus 30",
        "show deadline",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["2025-07-31"]


# ---------------------------------------------------------------------------
# 8h — Interpreter: date tolerance (within)
# ---------------------------------------------------------------------------


def test_within_date_tolerance_passes():
    session, results = run_lines([
        "remember a date called d with 2025-07-15",
        "require d is within 30 of 2025-07-01",
    ])
    assert results[-1].status is ResultStatus.SUCCESS, results[-1].message


def test_within_date_tolerance_fails():
    session, results = run_lines([
        "remember a date called d with 2025-09-01",
        "require d is within 30 of 2025-07-01",
    ])
    assert results[-1].status is ResultStatus.REQUIREMENT_NOT_MET


def test_within_date_tolerance_exact_match():
    session, results = run_lines([
        "remember a date called d with 2025-07-01",
        "require d is within 0 of 2025-07-01",
    ])
    assert results[-1].status is ResultStatus.SUCCESS, results[-1].message


def test_within_tolerance_rejects_bare_date_at_parse_time():
    result = parse(tokenize("require x is within 2025-07-01 of target"))
    assert result.status is ResultStatus.ERROR_PARSE
    assert "within" in result.message


# ---------------------------------------------------------------------------
# 8i — Interpreter: today injection
# ---------------------------------------------------------------------------


def test_today_injection_resolves_in_condition():
    source = (
        "remember a date called due-date with 2025-07-01\n"
        "require due-date is below today\n"
    )
    result = run(source, inject={"today": date(2026, 1, 1)}, enter_phase2=False)
    assert not result.had_error
    assert result.results[-1].status is ResultStatus.SUCCESS


def test_today_injection_fails_condition_when_in_past():
    # REQUIREMENT_NOT_MET means "the data violates a rule", not a program
    # error — it deliberately doesn't set had_error (same as any other
    # failed `require`; see run.Session.record_result).
    source = (
        "remember a date called due-date with 2025-07-01\n"
        "require due-date is below today\n"
    )
    result = run(source, inject={"today": date(2020, 1, 1)}, enter_phase2=False)
    assert result.results[-1].status is ResultStatus.REQUIREMENT_NOT_MET


def test_no_injection_today_is_unresolved_name():
    source = "remember a number called x with 5\nrequire x is below today\n"
    result = run(source, enter_phase2=False)
    assert result.had_error
    last = result.results[-1]
    assert last.status is ResultStatus.ERROR_SEMANTIC
    assert "today" in last.message


def test_inject_additive_when_unreferenced():
    # A program that never mentions `today` is unaffected by its presence.
    source = "remember a value called x with 5\nshow x\n"
    result = run(source, inject={"today": date(2025, 7, 4)}, enter_phase2=False)
    assert not result.had_error
    assert result.results[-1].output == ["5"]


# ---------------------------------------------------------------------------
# 8j — Renderer round-trips
# ---------------------------------------------------------------------------


def _roundtrip(line: str) -> None:
    ast1 = parse(tokenize(line))
    assert not hasattr(ast1, "status"), getattr(ast1, "message", ast1)
    rendered = render(ast1)
    assert rendered == line
    ast2 = parse(tokenize(rendered))
    assert not hasattr(ast2, "status"), getattr(ast2, "message", ast2)
    assert ast1 == ast2


def test_render_date_literal_bare():
    node = DateLiteral(value=date(2025, 7, 1))
    assert render(node) == "2025-07-01"


@pytest.mark.parametrize(
    "src",
    [
        "remember a date called d with 2025-07-01",
        "remember an order called o1 with filed-date as 2025-07-01",
        "remember a list called deadlines with 2025-07-01 and 2025-08-01",
        "require d is below 2025-12-31",
        "require d is within 30 of 2025-07-01",
        "remember a date called later from d plus 30",
    ],
)
def test_date_programs_round_trip(src):
    _roundtrip(src)


def test_starting_bare_date_round_trips_as_quoted_canonical_form():
    # starting/until always canonicalize to quoted form, whether the
    # source used a bare date or a quoted one.
    node = parse(tokenize("starting 2025-07-01 require x is above 10"))
    rendered = render(node)
    assert rendered == 'starting "2025-07-01" require x is above 10'
    node2 = parse(tokenize(rendered))
    assert node2 == node


# ---------------------------------------------------------------------------
# 8k — Backward compatibility
# ---------------------------------------------------------------------------


def test_quoted_date_stays_string_type():
    session, results = run_lines([
        'remember a value called s with "2025-07-01"',
        "show s",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert session.symtab["s"].type == "string"
    assert session.symtab["s"].value == "2025-07-01"
    assert results[-1].output == ["2025-07-01"]


def test_existing_numeric_arithmetic_unaffected():
    session, results = run_lines([
        "remember a value called price with 100",
        "remember a value called tax with 15",
        "remember a value called total from price plus tax",
        "show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["115"]


def test_existing_string_list_unaffected():
    session, results = run_lines([
        "remember a list called tags with \"a\" and \"b\"",
    ])
    assert results[-1].status is ResultStatus.SUCCESS, results[-1].message
    assert session.symtab["tags"].type == "list_of_strings"

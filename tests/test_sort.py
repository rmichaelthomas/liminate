"""Integration tests for the Infrastructure Era batch 2 `sort` verb and
`reverse` modifier — sentences 154–164.

Each test runs the program through the full pipeline via Session.run_line.
"""

from __future__ import annotations

from liminate.cli import Session
from liminate.result import ResultStatus


def run_lines(lines):
    session = Session()
    results = [session.run_line(line) for line in lines]
    return session, results


# ---------------------------------------------------------------------------
# Sentence 154 — ascending sort by numeric field
# ---------------------------------------------------------------------------


def test_sentence_154_ascending_sort_by_number():
    session, results = run_lines([
        "remember an order called o1 with total as 75",
        "remember an order called o2 with total as 30",
        "remember an order called o3 with total as 120",
        "remember a list called orders with o1 and o2 and o3",
        "sort the orders by total",
        "each the orders show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["30", "75", "120"]


# ---------------------------------------------------------------------------
# Sentence 155 — descending sort with `in reverse`
# ---------------------------------------------------------------------------


def test_sentence_155_descending_with_in_reverse():
    session, results = run_lines([
        "remember an order called o1 with total as 75",
        "remember an order called o2 with total as 30",
        "remember an order called o3 with total as 120",
        "remember a list called orders with o1 and o2 and o3",
        "sort the orders by total in reverse",
        "each the orders show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["120", "75", "30"]


# ---------------------------------------------------------------------------
# Sentence 156 — descending sort with bare `reverse`
# ---------------------------------------------------------------------------


def test_sentence_156_descending_with_bare_reverse():
    session, results = run_lines([
        "remember an order called o1 with total as 75",
        "remember an order called o2 with total as 30",
        "remember a list called orders with o1 and o2",
        "sort orders by total reverse",
        "each the orders show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["75", "30"]


# ---------------------------------------------------------------------------
# Sentence 157 — sort by string field (alphabetical)
# ---------------------------------------------------------------------------


def test_sentence_157_sort_by_string_field():
    session, results = run_lines([
        "remember a person called p1 with name as charlie",
        "remember a person called p2 with name as alice",
        "remember a person called p3 with name as bob",
        "remember a list called people with p1 and p2 and p3",
        "sort the people by name",
        "each the people show name",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["alice", "bob", "charlie"]


# ---------------------------------------------------------------------------
# Sentence 158 — sort preserves other fields
# ---------------------------------------------------------------------------


def test_sentence_158_sort_preserves_other_fields():
    session, results = run_lines([
        "remember an order called o1 with total as 75 and status as active",
        "remember an order called o2 with total as 30 and status as pending",
        "remember a list called orders with o1 and o2",
        "sort the orders by total",
        "each the orders show total and status",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == [
        "total: 30, status: pending",
        "total: 75, status: active",
    ]


# ---------------------------------------------------------------------------
# Sentence 159 — sort empty list (no error, no output)
# ---------------------------------------------------------------------------


def test_sentence_159_sort_empty_list_is_noop():
    session, results = run_lines([
        "remember an order called o1 with total as 999",
        "remember a list called orders with o1",
        "filter the orders where total is above 10000",
        "sort the orders by total",
        "count the orders",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["0"]


# ---------------------------------------------------------------------------
# Sentence 160 — sort then filter (operations compose)
# ---------------------------------------------------------------------------


def test_sentence_160_sort_then_filter():
    session, results = run_lines([
        "remember an order called o1 with total as 75",
        "remember an order called o2 with total as 30",
        "remember an order called o3 with total as 120",
        "remember a list called orders with o1 and o2 and o3",
        "sort the orders by total",
        "filter the orders where total is above 50",
        "each the orders show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["75", "120"]


# ---------------------------------------------------------------------------
# Sentence 161 — sort on non-list target (semantic error)
# ---------------------------------------------------------------------------


def test_sentence_161_sort_non_list_errors():
    session, results = run_lines([
        "remember a value called total with 100",
        "sort total by amount",
    ])
    assert results[0].status is ResultStatus.SUCCESS, results[0].message
    assert results[1].status is ResultStatus.ERROR_SEMANTIC
    assert "I can only sort a list" in (results[1].message or "")
    assert "total" in (results[1].message or "")


# ---------------------------------------------------------------------------
# Sentence 162 — sort by missing field (semantic error)
# ---------------------------------------------------------------------------


def test_sentence_162_sort_by_missing_field_errors():
    session, results = run_lines([
        "remember an order called o1 with total as 75",
        "remember a list called orders with o1",
        "sort the orders by missing-field",
    ])
    for r in results[:2]:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "missing-field" in (results[-1].message or "")


# ---------------------------------------------------------------------------
# Sentence 163 — sort inside an `and`-sequenced operation pair
# ---------------------------------------------------------------------------


def test_sentence_163_sort_inside_operation_sequence():
    session, results = run_lines([
        "remember an order called o1 with total as 75",
        "remember an order called o2 with total as 30",
        "remember a list called orders with o1 and o2",
        "sort the orders by total and each the orders show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["30", "75"]


# ---------------------------------------------------------------------------
# Sentence 164 — sort with `then` sequencing
# ---------------------------------------------------------------------------


def test_sentence_164_sort_with_then_sequencing():
    session, results = run_lines([
        "remember an order called o1 with total as 75",
        "remember an order called o2 with total as 30",
        "remember a list called orders with o1 and o2",
        "sort the orders by total then each the orders show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["30", "75"]


# ---------------------------------------------------------------------------
# `reverse` is a reserved word — rejected as a variable name
# ---------------------------------------------------------------------------


def test_reverse_is_reserved_as_a_name():
    session, results = run_lines([
        "remember a value called reverse with 5",
    ])
    assert results[0].status is ResultStatus.ERROR_PARSE
    assert "reverse" in (results[0].message or "")
    assert "operator" in (results[0].message or "")


# ---------------------------------------------------------------------------
# `in` is NOT reserved — usable as a variable name
# ---------------------------------------------------------------------------


def test_in_is_not_reserved():
    from liminate.vocabulary import (
        ALL_RESERVED, ARTICLES, CONNECTIVES, MULTI_WORD_RESERVED, OPERATORS,
        V2_RESERVED, VERBS,
    )
    assert "in" not in ALL_RESERVED
    for s in (VERBS, CONNECTIVES, OPERATORS, ARTICLES,
              V2_RESERVED, MULTI_WORD_RESERVED):
        assert "in" not in s


# ---------------------------------------------------------------------------
# Canonical rendering round-trip
# ---------------------------------------------------------------------------


def test_sort_renders_canonically():
    from liminate.lexer import tokenize
    from liminate.parser import parse
    from liminate.renderer import render

    for src in (
        "sort the orders by total",
        "sort the orders by total in reverse",
    ):
        ast = parse(tokenize(src))
        assert parse(tokenize(render(ast))) == ast

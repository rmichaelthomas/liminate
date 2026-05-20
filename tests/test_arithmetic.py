"""Integration tests for the Infrastructure Era arithmetic operators —
sentences 140–153. Covers basic +/-/*/÷, PEMDAS precedence, left-to-right
associativity, mixed-tier expressions, arithmetic in condition right-hand
sides, arithmetic inside `each` action bodies, division by zero, and
arithmetic over `of` field access.

Each test runs the program through the full pipeline via Session.run_line.
"""

from __future__ import annotations

from liminate.cli import Session
from liminate.result import ResultStatus


def run_lines(lines):
    session = Session()
    results = [session.run_line(line) for line in lines]
    return session, results


def _last_output(results):
    return results[-1].output


# ---------------------------------------------------------------------------
# Sentence 140 — basic addition
# ---------------------------------------------------------------------------


def test_sentence_140_basic_addition():
    session, results = run_lines([
        "remember a value called price with 100",
        "remember a value called tax with 15",
        "remember a value called total from price plus tax",
        "show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["115"]


# ---------------------------------------------------------------------------
# Sentence 141 — basic subtraction
# ---------------------------------------------------------------------------


def test_sentence_141_basic_subtraction():
    session, results = run_lines([
        "remember a value called gross with 200",
        "remember a value called fees with 35",
        "remember a value called net from gross minus fees",
        "show net",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["165"]


# ---------------------------------------------------------------------------
# Sentence 142 — basic multiplication
# ---------------------------------------------------------------------------


def test_sentence_142_basic_multiplication():
    session, results = run_lines([
        "remember a value called rate with 25",
        "remember a value called hours with 8",
        "remember a value called pay from rate multiplied by hours",
        "show pay",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["200"]


# ---------------------------------------------------------------------------
# Sentence 143 — basic division
# ---------------------------------------------------------------------------


def test_sentence_143_basic_division():
    session, results = run_lines([
        "remember a value called total with 150",
        "remember a value called people with 3",
        "remember a value called share from total divided by people",
        "show share",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["50"]


# ---------------------------------------------------------------------------
# Sentence 144 — PEMDAS: multiply before add
# ---------------------------------------------------------------------------


def test_sentence_144_pemdas_multiply_before_add():
    session, results = run_lines([
        "remember a value called base with 10",
        "remember a value called bonus with 5",
        "remember a value called multiplier with 3",
        "remember a value called result from base plus bonus multiplied by multiplier",
        "show result",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    # bonus * multiplier = 15, then base + 15 = 25 (not (base + bonus) * multiplier = 45)
    assert results[-1].output == ["25"]


# ---------------------------------------------------------------------------
# Sentence 145 — PEMDAS: divide before subtract
# ---------------------------------------------------------------------------


def test_sentence_145_pemdas_divide_before_subtract():
    session, results = run_lines([
        "remember a value called budget with 100",
        "remember a value called months with 4",
        "remember a value called spent with 10",
        "remember a value called remaining from budget minus spent divided by months",
        "show remaining",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    # spent / months = 2.5, then budget - 2.5 = 97.5
    assert results[-1].output == ["97.5"]


# ---------------------------------------------------------------------------
# Sentence 146 — left-to-right within the same tier
# ---------------------------------------------------------------------------


def test_sentence_146_left_to_right_same_tier():
    session, results = run_lines([
        "remember a value called a-val with 20",
        "remember a value called b-val with 5",
        "remember a value called c-val with 3",
        "remember a value called result from a-val minus b-val minus c-val",
        "show result",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    # (20 - 5) - 3 = 12, not 20 - (5 - 3) = 18
    assert results[-1].output == ["12"]


# ---------------------------------------------------------------------------
# Sentence 147 — arithmetic with literal numbers
# ---------------------------------------------------------------------------


def test_sentence_147_arithmetic_with_literal_numbers():
    session, results = run_lines([
        "remember a value called price with 50",
        "remember a value called total from price multiplied by 2",
        "show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["100"]


# ---------------------------------------------------------------------------
# Sentence 148 — arithmetic on right-hand side of a condition
# ---------------------------------------------------------------------------


def test_sentence_148_arithmetic_in_condition_rhs():
    session, results = run_lines([
        "remember a value called base with 40",
        "remember a value called discount with 10",
        "remember an order called o1 with total as 75",
        "remember an order called o2 with total as 25",
        "remember a list called orders with o1 and o2",
        "keep the orders where total is above base minus discount",
        "count the orders",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    # base - discount = 30. o1 (total 75) > 30 → kept. o2 (total 25) → dropped.
    # `keep` is non-destructive (returns matching list, source unchanged).
    # The `count` here counts the original orders list — both items.
    # However the meaningful check is that the keep output is one record.
    keep_output = results[-2].output
    assert keep_output is not None
    assert len(keep_output) == 1


# ---------------------------------------------------------------------------
# Sentence 149 — arithmetic inside `each` action body
# ---------------------------------------------------------------------------


def test_sentence_149_arithmetic_in_each_body():
    session, results = run_lines([
        "remember a value called tax-rate with 0.1",
        "remember an order called o1 with total as 100",
        "remember an order called o2 with total as 200",
        "remember a list called orders with o1 and o2",
        "remember a list called taxes with 0",
        "each the orders add total multiplied by tax-rate to taxes",
        "show taxes",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    # taxes seeded with 0; then 100*0.1=10 and 200*0.1=20 appended.
    assert results[-1].output == ["0, 10, 20"]


# ---------------------------------------------------------------------------
# Sentence 150 — division by zero
# ---------------------------------------------------------------------------


def test_sentence_150_division_by_zero():
    session, results = run_lines([
        "remember a value called x with 10",
        "remember a value called y with 0",
        "remember a value called z from x divided by y",
    ])
    for r in results[:2]:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "divide by zero" in (results[-1].message or "")


# ---------------------------------------------------------------------------
# Sentence 151 — arithmetic with field access via `of`
# ---------------------------------------------------------------------------


def test_sentence_151_arithmetic_with_field_access():
    session, results = run_lines([
        "remember an order called myorder with price as 100 and quantity as 3",
        "remember a value called line-total from price of myorder multiplied by quantity of myorder",
        "show line-total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["300"]


# ---------------------------------------------------------------------------
# Sentence 152 — chained arithmetic (three operations, same tier)
# ---------------------------------------------------------------------------


def test_sentence_152_chained_arithmetic_same_tier():
    session, results = run_lines([
        "remember a value called a-val with 10",
        "remember a value called b-val with 20",
        "remember a value called c-val with 30",
        "remember a value called sum-val from a-val plus b-val plus c-val",
        "show sum-val",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["60"]


# ---------------------------------------------------------------------------
# Sentence 153 — mixed tiers, multiple operations
# ---------------------------------------------------------------------------


def test_sentence_153_mixed_tiers_multiple_operations():
    session, results = run_lines([
        "remember a value called price with 100",
        "remember a value called qty with 2",
        "remember a value called discount with 10",
        "remember a value called shipping with 5",
        "remember a value called total from price multiplied by qty minus discount plus shipping",
        "show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    # price * qty = 200, then 200 - 10 + 5 = 195 (left-to-right on additive tier)
    assert results[-1].output == ["195"]


# ---------------------------------------------------------------------------
# Failure mode #1 — standalone `by` connective still works
# ---------------------------------------------------------------------------


def test_standalone_by_is_a_connective():
    """The multi-word lookahead fires only when `multiplied` or `divided`
    precedes `by`. A bare `by` falls through to the CONNECTIVES table so
    future verbs (e.g., `transform`) can use it. We verify this at the
    token level — `by` lexes as CONNECTIVE on its own."""
    from liminate.lexer import tokenize
    from liminate.vocabulary import TokenType

    toks = tokenize("something by name")
    assert toks[1].type is TokenType.CONNECTIVE
    assert toks[1].value == "by"


# ---------------------------------------------------------------------------
# Canonical rendering round-trip
# ---------------------------------------------------------------------------


def test_arithmetic_renders_canonically():
    from liminate.lexer import tokenize
    from liminate.parser import parse
    from liminate.renderer import render

    src = "remember a value called total from price multiplied by qty plus shipping"
    ast = parse(tokenize(src))
    rendered = render(ast)
    # Re-parsing the rendered form must produce the same AST.
    assert parse(tokenize(rendered)) == ast

"""Integration tests for the final V2-promoted `transform` verb —
sentences 178–192. `transform` mutates list elements in place in two
modes: record-field (`transform <field> of <list> by <expr>`) and
scalar-list (`transform <list> by <expr>`). The expression is evaluated
per element with iterator context.

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
# Sentence 178 — record-field: subtract a constant
# ---------------------------------------------------------------------------


def test_sentence_178_record_field_subtract_constant():
    session, results = run_lines([
        "remember an order called o1 with total as 100",
        "remember an order called o2 with total as 200",
        "remember a list called orders with o1 and o2",
        "transform total of the orders by total minus 10",
        "each the orders show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["90", "190"]


# ---------------------------------------------------------------------------
# Sentence 179 — record-field: multiply by a fraction (discount)
# ---------------------------------------------------------------------------


def test_sentence_179_record_field_multiply_fraction():
    session, results = run_lines([
        "remember an item called i1 with price as 100",
        "remember an item called i2 with price as 50",
        "remember a list called items with i1 and i2",
        "transform price of the items by price multiplied by 0.9",
        "each the items show price",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    # 100*0.9 = 90.0 and 50*0.9 = 45.0, displayed as whole numbers per
    # Liminate's _format_scalar convention (whole floats render as ints,
    # same as `10 divided by 2` → `5`).
    assert results[-1].output == ["90", "45"]


# ---------------------------------------------------------------------------
# Sentence 180 — record-field: use a symbol-table variable
# ---------------------------------------------------------------------------


def test_sentence_180_record_field_symbol_variable():
    session, results = run_lines([
        "remember a value called discount with 15",
        "remember an order called o1 with total as 100",
        "remember an order called o2 with total as 75",
        "remember a list called orders with o1 and o2",
        "transform total of the orders by total minus discount",
        "each the orders show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["85", "60"]


# ---------------------------------------------------------------------------
# Sentence 181 — record-field: preserves other fields
# ---------------------------------------------------------------------------


def test_sentence_181_record_field_preserves_others():
    session, results = run_lines([
        "remember an order called o1 with total as 100 and status as active",
        "remember a list called orders with o1",
        "transform total of the orders by total plus 50",
        "each the orders show total and status",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["total: 150, status: active"]


# ---------------------------------------------------------------------------
# Sentence 182 — scalar-list: add a constant
# ---------------------------------------------------------------------------


def test_sentence_182_scalar_add_constant():
    session, results = run_lines([
        "remember a list called scores with 10 and 20 and 30",
        "transform the scores by each plus 5",
        "show scores",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["15, 25, 35"]


# ---------------------------------------------------------------------------
# Sentence 183 — scalar-list: multiply
# ---------------------------------------------------------------------------


def test_sentence_183_scalar_multiply():
    session, results = run_lines([
        "remember a list called prices with 100 and 200 and 50",
        "transform prices by each multiplied by 2",
        "show prices",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["200, 400, 100"]


# ---------------------------------------------------------------------------
# Sentence 184 — scalar-list: subtract
# ---------------------------------------------------------------------------


def test_sentence_184_scalar_subtract():
    session, results = run_lines([
        "remember a list called values with 50 and 30 and 10",
        "transform the values by each minus 5",
        "show values",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["45, 25, 5"]


# ---------------------------------------------------------------------------
# Sentence 185 — transform then show (operation sequence)
# ---------------------------------------------------------------------------


def test_sentence_185_transform_then_show_sequence():
    session, results = run_lines([
        "remember an order called o1 with total as 100",
        "remember an order called o2 with total as 50",
        "remember a list called orders with o1 and o2",
        "transform total of the orders by total plus 25 and each the orders show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["125", "75"]


# ---------------------------------------------------------------------------
# Sentence 186 — transform then sort (composition)
# ---------------------------------------------------------------------------


def test_sentence_186_transform_then_sort():
    session, results = run_lines([
        "remember an order called o1 with total as 100",
        "remember an order called o2 with total as 200",
        "remember an order called o3 with total as 50",
        "remember a list called orders with o1 and o2 and o3",
        "transform total of the orders by total multiplied by 2",
        "sort the orders by total",
        "each the orders show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["100", "200", "400"]


# ---------------------------------------------------------------------------
# Sentence 187 — transform empty list (no error)
# ---------------------------------------------------------------------------


def test_sentence_187_transform_empty_list_noop():
    session, results = run_lines([
        "remember an order called o1 with total as 999",
        "remember a list called orders with o1",
        "filter the orders where total is above 10000",
        "transform total of the orders by total plus 1",
        "count the orders",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["0"]


# ---------------------------------------------------------------------------
# Sentence 188 — transform non-record in field mode (error)
# ---------------------------------------------------------------------------


def test_sentence_188_transform_non_record_errors():
    session, results = run_lines([
        "remember a list called nums with 1 and 2 and 3",
        "transform total of the nums by total plus 1",
    ])
    assert results[0].status is ResultStatus.SUCCESS, results[0].message
    assert results[1].status is ResultStatus.ERROR_SEMANTIC
    assert "records" in (results[1].message or "")


# ---------------------------------------------------------------------------
# Sentence 189 — transform missing field (error)
# ---------------------------------------------------------------------------


def test_sentence_189_transform_missing_field_errors():
    session, results = run_lines([
        "remember an order called o1 with total as 100",
        "remember a list called orders with o1",
        "transform missing-field of the orders by missing-field plus 1",
    ])
    for r in results[:2]:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "missing-field" in (results[-1].message or "")


# ---------------------------------------------------------------------------
# Sentence 190 — transform with PEMDAS in expression
# ---------------------------------------------------------------------------


def test_sentence_190_transform_pemdas_expression():
    session, results = run_lines([
        "remember a value called base with 10",
        "remember a value called rate with 2",
        "remember an order called o1 with total as 100",
        "remember a list called orders with o1",
        "transform total of the orders by total plus base multiplied by rate",
        "each the orders show total",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    # base * rate = 20, then total + 20 = 120 (PEMDAS).
    assert results[-1].output == ["120"]


# ---------------------------------------------------------------------------
# Sentence 191 — transform with field access in expression
# ---------------------------------------------------------------------------


def test_sentence_191_transform_field_access_expression():
    session, results = run_lines([
        "remember an order called o1 with price as 100 and quantity as 3",
        "remember a list called orders with o1",
        "transform price of the orders by price multiplied by quantity",
        "each the orders show price",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    # Both `price` and `quantity` resolve against the current record.
    assert results[-1].output == ["300"]


# ---------------------------------------------------------------------------
# Sentence 192 — scalar transform with division
# ---------------------------------------------------------------------------


def test_sentence_192_scalar_division():
    session, results = run_lines([
        "remember a list called amounts with 100 and 200 and 50",
        "transform the amounts by each divided by 2",
        "show amounts",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["50, 100, 25"]


# ---------------------------------------------------------------------------
# transform is now a verb; V2_RESERVED is empty
# ---------------------------------------------------------------------------


def test_transform_reserved_category_is_verb():
    from liminate.vocabulary import reserved_category, VERBS, V2_RESERVED

    assert reserved_category("transform") == "verb"
    assert "transform" in VERBS
    assert "transform" not in V2_RESERVED
    assert len(V2_RESERVED) == 0


def test_transform_rejected_as_a_name():
    session, results = run_lines([
        "remember a value called transform with 5",
    ])
    assert results[0].status is ResultStatus.ERROR_PARSE
    assert "transform" in (results[0].message or "")
    assert "verb" in (results[0].message or "")


# ---------------------------------------------------------------------------
# Missing `by` / `of`-or-`by` errors
# ---------------------------------------------------------------------------


def test_transform_missing_by_errors():
    session, results = run_lines([
        "remember an order called o1 with total as 100",
        "remember a list called orders with o1",
        "transform total of the orders",
    ])
    assert results[-1].status is ResultStatus.ERROR_PARSE
    assert "by" in (results[-1].message or "")


# ---------------------------------------------------------------------------
# Canonical rendering round-trip (both modes)
# ---------------------------------------------------------------------------


def test_transform_renders_canonically():
    from liminate.lexer import tokenize
    from liminate.parser import parse
    from liminate.renderer import render

    for src in (
        "transform total of the orders by total minus discount",
        "transform the numbers by each plus 10",
    ):
        ast = parse(tokenize(src))
        assert parse(tokenize(render(ast))) == ast

"""Integration tests for Liminate `add` v1 §11 — sentences 128–139.

Each test runs the program through the full pipeline (lex → reorder →
parse → analyze → execute) via Session.run_line, and asserts the
expected output or error message verbatim from the specification.
"""

from __future__ import annotations

from liminate.cli import Session
from liminate.result import ResultStatus


def run_lines(lines):
    session = Session()
    results = [session.run_line(line) for line in lines]
    return session, results


# ---------------------------------------------------------------------------
# Sentence 128 — record into list of records (count after add)
# ---------------------------------------------------------------------------


def test_sentence_128_add_record_to_list_of_records():
    session, results = run_lines([
        "remember an order called o1 with total as 75 and status as active",
        "remember an order called o2 with total as 30 and status as pending",
        "remember a list called orders with o1",
        "add o2 to the orders",
        "count the orders",
    ])
    for r in results[:4]:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[3].output is None  # silent
    assert results[4].output == ["2"]
    assert len(session.symtab["orders"].value) == 2


# ---------------------------------------------------------------------------
# Sentence 129 — number into list of numbers
# ---------------------------------------------------------------------------


def test_sentence_129_add_number_to_list_of_numbers():
    session, results = run_lines([
        "remember a list called scores with 10 and 20",
        "add 30 to scores",
        "show scores",
    ])
    assert results[1].status is ResultStatus.SUCCESS
    assert results[1].output is None
    assert results[2].output == ["10, 20, 30"]
    assert session.symtab["scores"].value == [10, 20, 30]


# ---------------------------------------------------------------------------
# Sentence 130 — string into list of strings
# ---------------------------------------------------------------------------


def test_sentence_130_add_string_to_list_of_strings():
    session, results = run_lines([
        "remember a list called names with alice and bob",
        "add charlie to the names",
        "show names",
    ])
    assert results[1].status is ResultStatus.SUCCESS
    assert results[2].output == ["alice, bob, charlie"]


# ---------------------------------------------------------------------------
# Sentence 131 — type mismatch: number → list of strings
# ---------------------------------------------------------------------------


def test_sentence_131_add_number_to_list_of_strings_is_error():
    _, results = run_lines([
        "remember a list called words with hello and world",
        "add 42 to words",
    ])
    assert results[1].status is ResultStatus.ERROR_SEMANTIC
    assert results[1].message == (
        "'words' is a list of text. '42' is a number and can't be added to it."
    )


# ---------------------------------------------------------------------------
# Sentence 132 — type mismatch: string → list of numbers
# ---------------------------------------------------------------------------


def test_sentence_132_add_string_to_list_of_numbers_is_error():
    _, results = run_lines([
        "remember a list called values with 1 and 2 and 3",
        "add oops to values",
    ])
    assert results[1].status is ResultStatus.ERROR_SEMANTIC
    assert results[1].message == (
        "'values' is a list of numbers. 'oops' is text and can't be added to it."
    )


# ---------------------------------------------------------------------------
# Sentence 133 — non-list target
# ---------------------------------------------------------------------------


def test_sentence_133_add_to_non_list_is_error():
    _, results = run_lines([
        "remember a value called total with 100",
        "add 5 to total",
    ])
    assert results[1].status is ResultStatus.ERROR_SEMANTIC
    assert results[1].message == "I can only add to a list. 'total' is a number."


# ---------------------------------------------------------------------------
# Sentence 134 — accumulation inside `each`
# ---------------------------------------------------------------------------


def test_sentence_134_add_inside_each_accumulation():
    session, results = run_lines([
        "remember an order called o1 with total as 75",
        "remember an order called o2 with total as 30",
        "remember an order called o3 with total as 120",
        "remember a list called orders with o1 and o2 and o3",
        "remember a list called big-totals with 0",
        "each the orders add total to big-totals",
        "show big-totals",
    ])
    assert results[5].status is ResultStatus.SUCCESS, results[5].message
    assert results[6].output == ["0, 75, 30, 120"]
    assert session.symtab["big-totals"].value == [0, 75, 30, 120]


# ---------------------------------------------------------------------------
# Sentence 135 — self-mutation guard inside `each`
# ---------------------------------------------------------------------------


def test_sentence_135_add_inside_each_self_mutation_is_error():
    _, results = run_lines([
        "remember a list called items with 1 and 2 and 3",
        "each the items add 99 to items",
    ])
    assert results[1].status is ResultStatus.ERROR_SEMANTIC
    assert results[1].message == (
        "'items' is the list being iterated — you can't add to it while "
        "iterating. Try adding to a different list."
    )


# ---------------------------------------------------------------------------
# Sentence 136 — `add` inside a `choose` branch
# ---------------------------------------------------------------------------


def test_sentence_136_add_inside_choose_branch():
    session, results = run_lines([
        "remember a value called level with 75",
        "remember a list called alerts with none",
        "choose if level is above 50: add level to the alerts",
        "show alerts",
    ])
    assert results[2].status is ResultStatus.SUCCESS, results[2].message
    assert results[3].output == ["75"]


# ---------------------------------------------------------------------------
# Sentence 137 — mixed-schema record added to list of records
# ---------------------------------------------------------------------------


def test_sentence_137_add_mixed_schema_record():
    session, results = run_lines([
        "remember an order called o1 with total as 75 and status as active",
        "remember an item called item1 with name as widget and price as 10",
        "remember a list called things with o1",
        "add item1 to things",
        "count things",
    ])
    assert results[3].status is ResultStatus.SUCCESS, results[3].message
    assert results[4].output == ["2"]


# ---------------------------------------------------------------------------
# Sentence 138 — articles in both positions
# ---------------------------------------------------------------------------


def test_sentence_138_add_with_articles_both_positions():
    session, results = run_lines([
        "remember a list called numbers with 1 and 2",
        "add the 3 to the numbers",
        "show numbers",
    ])
    assert results[1].status is ResultStatus.SUCCESS, results[1].message
    assert results[1].canonical == "add 3 to numbers"
    assert results[2].output == ["1, 2, 3"]


# ---------------------------------------------------------------------------
# Sentence 139 — `add` is reserved and cannot be a user name
# ---------------------------------------------------------------------------


def test_sentence_139_add_reserved_as_name_is_error():
    _, results = run_lines([
        "remember a value called add with 5",
    ])
    assert results[0].status is ResultStatus.ERROR_PARSE
    assert results[0].message == (
        "The word 'add' is reserved in Liminate — it's used as a verb. "
        "Please choose a different name."
    )

"""Integration tests for the V2-promoted `compare` verb — sentences
165–177. `compare <left> to <right>` infers comparison mode from operand
types and stores a `comparison` record with `status` and `divergences`
fields.

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
# Sentence 165 — compare identical records (match)
# ---------------------------------------------------------------------------


def test_sentence_165_identical_records_match():
    session, results = run_lines([
        "remember an order called original with total as 75 and status as active",
        "remember an order called copy with total as 75 and status as active",
        "compare original to copy",
        "show status of comparison",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["match"]


# ---------------------------------------------------------------------------
# Sentence 166 — records differing on one field (mismatch)
# ---------------------------------------------------------------------------


def test_sentence_166_one_field_differs():
    session, results = run_lines([
        "remember an order called v1 with total as 75 and status as active",
        "remember an order called v2 with total as 75 and status as pending",
        "compare v1 to v2",
        "show status of comparison",
        "show divergences of comparison",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[3].output == ["mismatch"]
    assert results[4].output == ["status"]


# ---------------------------------------------------------------------------
# Sentence 167 — multiple fields differ (sorted divergences)
# ---------------------------------------------------------------------------


def test_sentence_167_multiple_fields_differ():
    session, results = run_lines([
        "remember an order called old with total as 50 and status as pending",
        "remember an order called new with total as 75 and status as active",
        "compare old to new",
        "show status of comparison",
        "show divergences of comparison",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[3].output == ["mismatch"]
    # sorted alphabetically: status, total
    assert results[4].output == ["status, total"]


# ---------------------------------------------------------------------------
# Sentence 168 — extra field on one side
# ---------------------------------------------------------------------------


def test_sentence_168_extra_field():
    session, results = run_lines([
        "remember an order called base with total as 75",
        "remember an order called extended with total as 75 and priority as high",
        "compare base to extended",
        "show status of comparison",
        "show divergences of comparison",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[3].output == ["mismatch"]
    assert results[4].output == ["priority"]


# ---------------------------------------------------------------------------
# Sentence 169 — identical scalars (match)
# ---------------------------------------------------------------------------


def test_sentence_169_identical_scalars():
    session, results = run_lines([
        "remember a value called x with 42",
        "remember a value called y with 42",
        "compare x to y",
        "show status of comparison",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["match"]


# ---------------------------------------------------------------------------
# Sentence 170 — different scalars (mismatch, empty divergences)
# ---------------------------------------------------------------------------


def test_sentence_170_different_scalars():
    session, results = run_lines([
        "remember a value called x with 42",
        "remember a value called y with 99",
        "compare x to y",
        "show status of comparison",
        "show divergences of comparison",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[3].output == ["mismatch"]
    # Empty divergences list renders as a single empty-string line.
    assert results[4].output == [""]


# ---------------------------------------------------------------------------
# Sentence 171 — record vs scalar (type mismatch)
# ---------------------------------------------------------------------------


def test_sentence_171_record_vs_scalar_type_mismatch():
    session, results = run_lines([
        "remember an order called o1 with total as 75",
        "remember a value called x with 42",
        "compare o1 to x",
        "show status of comparison",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["type_mismatch"]


# ---------------------------------------------------------------------------
# Sentence 172 — identical lists (match)
# ---------------------------------------------------------------------------


def test_sentence_172_identical_lists():
    session, results = run_lines([
        "remember a list called nums-a with 1 and 2 and 3",
        "remember a list called nums-b with 1 and 2 and 3",
        "compare nums-a to nums-b",
        "show status of comparison",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["match"]


# ---------------------------------------------------------------------------
# Sentence 173 — lists with element difference (mismatch on index)
# ---------------------------------------------------------------------------


def test_sentence_173_list_element_differs():
    session, results = run_lines([
        "remember a list called nums-a with 1 and 2 and 3",
        "remember a list called nums-b with 1 and 99 and 3",
        "compare nums-a to nums-b",
        "show status of comparison",
        "show divergences of comparison",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[3].output == ["mismatch"]
    # Index 1 differs.
    assert results[4].output == ["1"]


# ---------------------------------------------------------------------------
# Sentence 174 — lists of different length
# ---------------------------------------------------------------------------


def test_sentence_174_lists_different_length():
    session, results = run_lines([
        "remember a list called short with 1 and 2",
        "remember a list called longer with 1 and 2 and 3",
        "compare short to longer",
        "show status of comparison",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["length_mismatch"]


# ---------------------------------------------------------------------------
# Sentence 175 — compare then branch with choose
# ---------------------------------------------------------------------------


def test_sentence_175_compare_then_choose():
    session, results = run_lines([
        "remember an order called submitted with total as 75 and status as pending",
        "remember an order called approved with total as 75 and status as active",
        "compare submitted to approved",
        'choose if status of comparison is equal to "match": show "identical" '
        'otherwise show "different"',
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["different"]


# ---------------------------------------------------------------------------
# Sentence 176 — capture divergences into a list and count them
# ---------------------------------------------------------------------------


def test_sentence_176_count_divergences():
    session, results = run_lines([
        "remember an order called v1 with total as 50 and status as pending and priority as low",
        "remember an order called v2 with total as 75 and status as active and priority as low",
        "compare v1 to v2",
        "remember a list called diffs from divergences of comparison",
        "count the diffs",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    # total and status differ; priority matches → 2 divergences.
    assert results[-1].output == ["2"]


# ---------------------------------------------------------------------------
# Sentence 177 — second compare overwrites the first result
# ---------------------------------------------------------------------------


def test_sentence_177_second_compare_overwrites():
    session, results = run_lines([
        "remember a value called x with 1",
        "remember a value called y with 1",
        "remember a value called z with 2",
        "compare x to y",
        "show status of comparison",
        "compare x to z",
        "show status of comparison",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[4].output == ["match"]
    assert results[6].output == ["mismatch"]


# ---------------------------------------------------------------------------
# compare is now a verb (was V2-reserved)
# ---------------------------------------------------------------------------


def test_compare_reserved_category_is_verb():
    from liminate.vocabulary import reserved_category, VERBS, V2_RESERVED

    assert reserved_category("compare") == "verb"
    assert "compare" in VERBS
    assert "compare" not in V2_RESERVED


def test_compare_rejected_as_a_name():
    session, results = run_lines([
        "remember a value called compare with 5",
    ])
    assert results[0].status is ResultStatus.ERROR_PARSE
    assert "compare" in (results[0].message or "")
    assert "verb" in (results[0].message or "")


# ---------------------------------------------------------------------------
# Analyzer — undefined operand
# ---------------------------------------------------------------------------


def test_compare_undefined_operand_errors():
    session, results = run_lines([
        "remember a value called x with 5",
        "compare x to missing-name",
    ])
    assert results[0].status is ResultStatus.SUCCESS
    assert results[1].status is ResultStatus.ERROR_SEMANTIC
    assert "missing-name" in (results[1].message or "")


# ---------------------------------------------------------------------------
# Canonical rendering round-trip
# ---------------------------------------------------------------------------


def test_compare_renders_canonically():
    from liminate.lexer import tokenize
    from liminate.parser import parse
    from liminate.renderer import render

    src = "compare order-a to order-b"
    ast = parse(tokenize(src))
    assert parse(tokenize(render(ast))) == ast

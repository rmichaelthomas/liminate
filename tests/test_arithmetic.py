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


# ---------------------------------------------------------------------------
# Negative number literals (regression: `-3` was lexed as text, so a number
# remembered as `-3` failed numeric comparisons with "requires numbers, but
# 't' is text"). The leading minus is now part of the NUMBER token.
# ---------------------------------------------------------------------------


def test_negative_number_literal_compares_as_number():
    session, results = run_lines([
        'remember a number called t with -3',
        'choose if t is below 0: show "neg" otherwise show "pos"',
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["neg"]


def test_negative_literal_on_condition_right_hand_side():
    session, results = run_lines([
        'remember a number called t with 5',
        'choose if t is above -3: show "above" otherwise show "below"',
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].output == ["above"]


def test_list_of_negative_numbers_is_numeric():
    session, results = run_lines([
        'remember a list called xs with -2 and 5 and -8',
        'show xs',
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message


# ---------------------------------------------------------------------------
# Arithmetic linearity restriction (Fable decidability condition (c)) —
# `multiplied_by`/`divided_by` reject when both operands are runtime-
# resolved, but ONLY as the value side of a deontic/choice condition
# (forbid/require/permit/expect/choose). Outside a condition —
# `remember ... with/from`, list items, `add <expr> to <list>` — nonlinear
# arithmetic is unrestricted; it never reaches the Z3 satisfiability
# encoder (Fable Step 2, not built yet).
# ---------------------------------------------------------------------------


def _semantic_message(results):
    return results[-1].message or ""


# ---------- reject: both operands runtime-resolved, inside a condition ----------


def test_forbid_condition_rejects_fact_times_fact():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "forbid alpha is above beta multiplied by beta",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    msg = _semantic_message(results)
    assert "at least one plain number" in msg
    assert "'beta' and 'beta'" in msg


def test_forbid_condition_rejects_fact_divided_by_fact():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "forbid alpha is above beta divided by beta",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "at least one plain number" in _semantic_message(results)


def test_forbid_condition_rejects_nested_fact_times_fact():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "forbid alpha is above beta multiplied by beta multiplied by 2",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "at least one plain number" in _semantic_message(results)


def test_require_condition_rejects_fact_times_fact():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "require alpha is above beta multiplied by beta",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "at least one plain number" in _semantic_message(results)


def test_permit_condition_rejects_fact_times_fact():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "permit alpha is above beta multiplied by beta",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "at least one plain number" in _semantic_message(results)


def test_expect_condition_rejects_fact_times_fact():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "expect alpha is above beta multiplied by beta",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "at least one plain number" in _semantic_message(results)


def test_choose_condition_rejects_fact_times_fact():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        'choose if alpha is above beta multiplied by beta: show "big" otherwise show "small"',
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "at least one plain number" in _semantic_message(results)


# ---------- pass: at least one literal operand, inside a condition (unchanged) ----------


def test_forbid_condition_allows_literal_times_literal():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "forbid alpha is above 3 multiplied by 4",
    ])
    assert results[-1].status is ResultStatus.SUCCESS


def test_forbid_condition_allows_fact_times_literal():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "forbid alpha is above beta multiplied by 3",
    ])
    assert results[-1].status is ResultStatus.PROHIBITION_VIOLATED


def test_forbid_condition_allows_literal_times_fact():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "forbid alpha is above 3 multiplied by beta",
    ])
    assert results[-1].status is ResultStatus.PROHIBITION_VIOLATED


def test_forbid_condition_allows_fact_plus_fact():
    """`plus`/`minus` are linear — no restriction in any operand
    combination."""
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "forbid alpha is above beta plus beta",
    ])
    assert results[-1].status is ResultStatus.PROHIBITION_VIOLATED


def test_forbid_condition_allows_fact_minus_fact():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "forbid alpha is above beta minus beta",
    ])
    assert results[-1].status is ResultStatus.PROHIBITION_VIOLATED


def test_forbid_condition_allows_all_literal_nested():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "forbid alpha is above 2 multiplied by 3 multiplied by 4",
    ])
    assert results[-1].status is ResultStatus.SUCCESS


# ---------- boundary pair: the restriction is condition-scoped, not global ----------
#
# These two tests document opposite sides of the same boundary and must be
# read together: the identical `beta multiplied by beta` expression passes
# outside a condition and rejects inside one. If a future change requires
# editing either one, it is very likely re-widening (or narrowing) the
# restriction's scope rather than fixing an unrelated bug — check the other
# test in the pair before touching either.


def test_fact_times_fact_passes_outside_a_condition():
    """`remember ... with/from` arithmetic never reaches the Z3 encoder,
    so it stays unrestricted — the non-deontic half of the boundary."""
    session, results = run_lines([
        "remember a number called beta with 2",
        "remember a number called z with beta multiplied by beta",
    ])
    for r in results:
        assert r.status is ResultStatus.SUCCESS, r.message


def test_fact_times_fact_rejects_inside_a_condition():
    """The same expression, as a condition value, rejects — the deontic
    half of the boundary."""
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "forbid alpha is above beta multiplied by beta",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC


# ---------- type-check precedence: linearity check fires last ----------


def test_text_in_condition_arithmetic_still_gives_text_error_not_linearity_error():
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        'forbid alpha is above "text" multiplied by beta',
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    msg = _semantic_message(results)
    assert "text" in msg.lower()
    assert "at least one plain number" not in msg


# ---------- date arithmetic message parity (untouched) ----------


def test_date_arithmetic_rejection_message_is_unchanged():
    session, results = run_lines([
        "remember a date called d1 with 2025-01-01",
        "remember a number called z with d1 multiplied by 2",
    ])
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    assert "can't be multiplied or divided" in _semantic_message(results).lower()


# ---------------------------------------------------------------------------
# Known gap — Fable decidability condition (c) remains OPEN. See the PR
# description / chain addendum for the full record. The restriction above
# only inspects a condition's own expression tree: it catches
# `beta multiplied by beta` written directly as a condition value, but not
# the same nonlinearity introduced through value indirection. Any
# remember-bound name whose value derives from fact × fact / fact ÷ fact
# reads as a plain NameRef in the condition AST, so the check never sees
# the ArithmeticNode. This is the common authoring form, not an edge case —
# closing it requires value provenance (taint at store time, a definition-
# site walk at analysis time, or resolving names to their defining
# expressions inside the future Z3 encoder). None of those are built yet.
# This test pins the CURRENT behaviour so it is impossible to miss when
# provenance work lands and this test needs to invert.
# ---------------------------------------------------------------------------


def test_KNOWN_GAP_value_indirection_bypasses_the_linearity_restriction():
    """Condition (c) is open, not closed. A nonlinear expression computed
    into a named value and then referenced in a condition currently
    PASSES analysis and evaluates — the restriction only sees the
    condition's own AST, which contains a bare NameRef, never the
    ArithmeticNode that produced it. See the addendum for the candidate
    provenance approaches under consideration."""
    session, results = run_lines([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "remember a value called doubled from beta multiplied by beta",
        "forbid alpha is above doubled",
    ])
    for r in results[:-1]:
        assert r.status is ResultStatus.SUCCESS, r.message
    assert results[-1].status is ResultStatus.PROHIBITION_VIOLATED

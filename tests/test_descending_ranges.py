"""Tests for D-6: descending ranges and step values for `gather`.

Covers:
- Descending ranges (`from 10 to 1`) count down inclusively.
- Step values (`by N`) for both ascending and descending ranges.
- The step is always positive; direction is derived from from/to.
- Parse errors for non-positive / non-numeric step values.
- Canonical rendering round-trips (with and without `by`).
- The range cap still applies, computed from the stepped span.
"""

from __future__ import annotations

import pytest

from liminate.lexer import tokenize
from liminate.parser import GatherNode, parse
from liminate.renderer import render
from liminate.result import ResultStatus

from tests._v3a_helpers import outputs, run_v3a


def _gather(src: str) -> list[int]:
    """Run a single gather line and return the stored list."""
    name = src.split()[2]  # `gather the <name> ...`
    session, results = run_v3a(src)
    errors = [r for r in results if r.status is not ResultStatus.SUCCESS]
    assert not errors, errors
    return session.symtab[name].value


# ---------------------------------------------------------------------------
# Descending ranges (no step)
# ---------------------------------------------------------------------------


def test_descending_basic():
    assert _gather("gather the countdown from 5 to 1") == [5, 4, 3, 2, 1]


def test_descending_to_ten_to_one():
    assert _gather("gather the nums from 10 to 1") == [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]


def test_single_element_endpoints_equal():
    assert _gather("gather the single from 3 to 3") == [3]


def test_ascending_unchanged():
    assert _gather("gather the sequence from 1 to 5") == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# Step values — ascending
# ---------------------------------------------------------------------------


def test_step_evens():
    assert _gather("gather the evens from 2 to 10 by 2") == [2, 4, 6, 8, 10]


def test_step_fives():
    assert _gather("gather the fives from 0 to 20 by 5") == [0, 5, 10, 15, 20]


def test_step_three_reaches_stop():
    assert _gather("gather the steps from 1 to 10 by 3") == [1, 4, 7, 10]


def test_step_three_stop_not_reached():
    assert _gather("gather the steps from 1 to 9 by 3") == [1, 4, 7]


# ---------------------------------------------------------------------------
# Step values — descending
# ---------------------------------------------------------------------------


def test_step_descending_by_two():
    assert _gather("gather the countdown from 10 to 1 by 2") == [10, 8, 6, 4, 2]


def test_step_descending_by_three_reaches_stop():
    assert _gather("gather the countdown from 10 to 1 by 3") == [10, 7, 4, 1]


def test_step_descending_by_three_stop_not_reached():
    assert _gather("gather the countdown from 10 to 2 by 3") == [10, 7, 4]


# ---------------------------------------------------------------------------
# Auto-show output
# ---------------------------------------------------------------------------


def test_descending_auto_shows():
    _, results = run_v3a("gather the countdown from 5 to 1")
    assert outputs(results) == ["5, 4, 3, 2, 1"]


def test_step_auto_shows():
    _, results = run_v3a("gather the evens from 2 to 10 by 2")
    assert outputs(results) == ["2, 4, 6, 8, 10"]


# ---------------------------------------------------------------------------
# Parse errors
# ---------------------------------------------------------------------------


def test_step_zero_is_parse_error():
    _, results = run_v3a("gather the x from 1 to 10 by 0")
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results
    assert "positive" in errors[0].message


def test_step_negative_is_parse_error():
    # `-2` is now a NUMBER token (negative literals are numbers), so this is
    # caught by the explicit positivity check on the step, same as `by 0`:
    # direction comes from from/to, never from a negative step.
    _, results = run_v3a("gather the x from 1 to 10 by -2")
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results
    assert "positive" in errors[0].message


def test_step_non_numeric_is_parse_error():
    _, results = run_v3a("gather the x from 1 to 10 by hello")
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results


# ---------------------------------------------------------------------------
# Range cap still applies (computed from the stepped span)
# ---------------------------------------------------------------------------


def test_range_cap_still_enforced_descending():
    _, results = run_v3a("gather the big from 20000 to 1")
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors, results
    assert "10,000" in errors[0].message


def test_step_reduces_size_under_cap():
    # 0..20000 by 5 → 4001 items, under the 10,000 cap.
    session, results = run_v3a("gather the strided from 0 to 20000 by 5")
    errors = [r for r in results if r.status is not ResultStatus.SUCCESS]
    assert not errors, errors
    assert len(session.symtab["strided"].value) == 4001


# ---------------------------------------------------------------------------
# Parser / AST
# ---------------------------------------------------------------------------


def test_parse_step_populates_step_val():
    ast = parse(tokenize("gather the evens from 2 to 10 by 2"))
    assert ast == GatherNode(name="evens", from_val=2, to_val=10, step_val=2)


def test_parse_no_step_leaves_step_val_none():
    ast = parse(tokenize("gather the nums from 1 to 10"))
    assert ast.step_val is None


# ---------------------------------------------------------------------------
# Canonical rendering round-trips
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "src,canonical",
    [
        ("gather the countdown from 5 to 1", "gather the countdown from 5 to 1"),
        ("gather the nums from 1 to 10", "gather the nums from 1 to 10"),
        ("gather the evens from 2 to 10 by 2", "gather the evens from 2 to 10 by 2"),
        ("gather the down from 100 to 1 by 10", "gather the down from 100 to 1 by 10"),
    ],
)
def test_canonical_rendering(src, canonical):
    assert render(parse(tokenize(src))) == canonical


def test_canonical_round_trip_descending():
    ast1 = parse(tokenize("gather the x from 10 to 1"))
    ast2 = parse(tokenize(render(ast1)))
    assert ast1 == ast2


def test_canonical_round_trip_step():
    ast1 = parse(tokenize("gather the x from 1 to 100 by 5"))
    ast2 = parse(tokenize(render(ast1)))
    assert ast1 == ast2


# ---------------------------------------------------------------------------
# Failure mode 2 — the `by` step is consumed cleanly and control returns to
# the operation-sequence loop for a following verb.
# ---------------------------------------------------------------------------


def test_gather_step_then_sequenced_verb_does_not_collide():
    session, results = run_v3a(
        "gather the nums from 1 to 10 by 2 and count nums"
    )
    errors = [r for r in results if r.status is not ResultStatus.SUCCESS]
    assert not errors, errors
    assert session.symtab["nums"].value == [1, 3, 5, 7, 9]
    assert outputs(results)[-1] == "5"

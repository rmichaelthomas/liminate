"""Phase 2 D-4 — analyzer-time deontic contradiction detection.

`detect_contradictions` is a static, warning-only pass over the top-level
ASTs of a program. It reports direct same-field logical conflicts between
`require` / `forbid` statements with simple (single-leaf) conditions. It
never blocks execution and never changes a result status.
"""

from liminate.analyzer import detect_contradictions
from liminate.cli import Session
from liminate.lexer import tokenize
from liminate.parser import parse
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus


def _parse(line):
    reordered = reorder(tokenize(line))
    assert not isinstance(reordered, LiminateResult), line
    ast = parse(reordered)
    assert not isinstance(ast, LiminateResult), line
    return ast


def warnings_for(lines):
    return detect_contradictions([_parse(l) for l in lines])


def run_lines(lines):
    session = Session()
    results = [session.run_line(line) for line in lines]
    return session, results


# ---------------------------------------------------------------------------
# 1–7 — the contradiction-rule table
# ---------------------------------------------------------------------------


def test_require_above_and_forbid_above_same_value_warns():
    """1. Rule 1 — identical operator+value, require vs forbid."""
    w = warnings_for(["require X is above 50", "forbid X is above 50"])
    assert len(w) == 1
    assert "contradiction" in w[0].lower()


def test_require_above_and_require_below_empty_range_warns():
    """2. Rule 2 — `above 50` and `below 30` leave no satisfying value."""
    w = warnings_for(["require X is above 50", "require X is below 30"])
    assert len(w) == 1


def test_require_above_and_require_below_satisfiable_range_no_warning():
    """3. `above 50` and `below 80` are jointly satisfiable — no warning."""
    w = warnings_for(["require X is above 50", "require X is below 80"])
    assert w == []


def test_require_equals_and_forbid_equals_same_value_warns():
    """4. Rule 1/3 — equality require vs equality forbid, same value."""
    w = warnings_for(["require X is value1", "forbid X is value1"])
    assert len(w) == 1


def test_require_equals_two_different_values_warns():
    """5. Rule 4 — two equality requirements with different values."""
    w = warnings_for(["require X is value1", "require X is value2"])
    assert len(w) == 1


def test_two_forbids_both_satisfiable_no_warning():
    """6. `forbid above 50` + `forbid below 30` — X in [30,50] satisfies both
    (rules 2 and 4 are require+require only)."""
    w = warnings_for(["forbid X is above 50", "forbid X is below 30"])
    assert w == []


def test_permit_never_contradicts():
    """7. `permit` is informational and never participates."""
    w = warnings_for(["require X is above 50", "permit X is above 50"])
    assert w == []


# ---------------------------------------------------------------------------
# 8–9 — trivial cases
# ---------------------------------------------------------------------------


def test_no_deontic_statements_no_warnings():
    """8. A program with no require/forbid produces no warnings."""
    w = warnings_for([
        "remember a number called X with 5",
        "show X",
    ])
    assert w == []


def test_single_require_no_warnings():
    """9. One requirement cannot contradict anything."""
    w = warnings_for(["require X is above 50"])
    assert w == []


# ---------------------------------------------------------------------------
# 10–11 — scope boundaries
# ---------------------------------------------------------------------------


def test_compound_condition_leaves_not_detected():
    """10. Compound (`and`/`or`) conditions are out of scope — even with
    contradicting leaves, no warning is emitted."""
    w = warnings_for([
        "require X is above 50 and X is below 30",
        "forbid X is above 50 and X is below 30",
    ])
    assert w == []


def test_different_fields_no_warning():
    """11. A conflict only exists when both statements target the same field."""
    w = warnings_for(["require X is above 50", "forbid Y is above 50"])
    assert w == []


# ---------------------------------------------------------------------------
# Extra coverage of the rule table (spec §3 design table rows)
# ---------------------------------------------------------------------------


def test_require_above_and_forbid_above_different_value_no_warning():
    """`require above 50` + `forbid above 80` — X in (50,80] satisfies both."""
    w = warnings_for(["require X is above 50", "forbid X is above 80"])
    assert w == []


def test_equality_via_is_equal_to_normalizes():
    """`is equal to` and bare `is` both mean equality (normalized)."""
    w = warnings_for(["require X is equal to 50", "forbid X is 50"])
    assert len(w) == 1


def test_quoted_string_equality_contradiction():
    """Quoted-string equality values participate like barewords."""
    w = warnings_for(['require X is "open"', 'forbid X is "open"'])
    assert len(w) == 1


def test_warning_names_both_statements_and_field():
    """The message identifies both statements and the shared field."""
    w = warnings_for(["require X is above 50", "forbid X is above 50"])
    assert "require x is above 50" in w[0]
    assert "forbid x is above 50" in w[0]
    assert "x" in w[0]


# ---------------------------------------------------------------------------
# 12 — integration: warning surfaces, execution is not blocked
# ---------------------------------------------------------------------------


def test_integration_contradiction_warns_without_blocking_execution():
    """12. A full program with a contradiction runs to completion; the
    warning appears in the output and execution is not halted by it."""
    session, results = run_lines([
        "remember a number called X with 99",
        "require X is above 50",
        "forbid X is above 80",
        "show X",
    ])
    # Without a contradiction the program would run identically; here we only
    # assert nothing was blocked by the analysis pass itself.
    assert results[0].status is ResultStatus.SUCCESS

    # Drive the same program through the whole-program loop to see the warning.
    from liminate.run import run as run_program
    source = "\n".join([
        "remember a number called X with 99",
        "require X is above 50",
        "forbid X is above 50",
        "show X",
    ])
    contract = run_program(source, enter_phase2=False)
    outputs = [line for r in contract.results if r and r.output for line in r.output]
    assert any(line.startswith("⚠") and "contradiction" in line.lower()
               for line in outputs)
    # `show X` still executed — execution was not blocked by the warning.
    assert any(line == "99" for line in outputs)
    # The advisory pass itself does not flip had_error.
    assert contract.results[0].status is ResultStatus.SUCCESS

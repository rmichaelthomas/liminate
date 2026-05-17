"""Integration tests for empty list construction (Liminate addendum v4).

Covers:
- `remember a list called X` with no `with` clause → empty list
- First `add` to an empty list infers element type correctly
- First `add` to a `none`-seeded list clears the sentinel
- Canonical rendering round-trip for empty lists
"""

from __future__ import annotations

from liminate.result import ResultStatus

from tests._v3a_helpers import outputs, run_v3a


# ---------------------------------------------------------------------------
# Empty list syntax
# ---------------------------------------------------------------------------


def test_el1_empty_list_parses():
    """remember a list called X with no `with` clause stores an empty list."""
    session, results = run_v3a("remember a list called items")
    successes = [r for r in results if r.status is ResultStatus.SUCCESS]
    assert len(successes) == 1
    assert session.symtab["items"].value == []


def test_el2_add_to_empty_list():
    """First add to an empty list produces a clean single-item list."""
    session, results = run_v3a(
        """
        remember a list called items
        add "a" to items
        """
    )
    errors = [r for r in results if r.status is not ResultStatus.SUCCESS]
    assert not errors, errors
    assert session.symtab["items"].value == ["a"]


def test_el3_multiple_adds_to_empty_list():
    """Multiple adds to an empty list accumulate cleanly."""
    session, results = run_v3a(
        """
        remember a list called items
        add "a" to items
        add "b" to items
        add "c" to items
        """
    )
    errors = [r for r in results if r.status is not ResultStatus.SUCCESS]
    assert not errors, errors
    assert session.symtab["items"].value == ["a", "b", "c"]


def test_el4_add_number_to_empty_list():
    """Adding a number to an empty list infers list_of_numbers type."""
    session, results = run_v3a(
        """
        remember a list called scores
        add 42 to scores
        """
    )
    errors = [r for r in results if r.status is not ResultStatus.SUCCESS]
    assert not errors, errors
    assert session.symtab["scores"].value == [42]
    assert session.symtab["scores"].type == "list_of_numbers"


def test_el5_show_empty_list():
    """show on an empty list produces empty output."""
    _, results = run_v3a(
        """
        remember a list called items
        show items
        """
    )
    successes = [r for r in results if r.status is ResultStatus.SUCCESS]
    assert len(successes) == 2


def test_el6_count_empty_list():
    """count on an empty list returns 0."""
    _, results = run_v3a(
        """
        remember a list called items
        count items
        """
    )
    assert outputs(results) == ["0"]


def test_el8_empty_form_requires_list_descriptor():
    """remember a value called X with no `with` is a parse error."""
    _, results = run_v3a("remember a value called x")
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results


def test_el9_canonical_round_trip():
    """Canonical rendering of an empty list has no `with` clause."""
    from liminate.lexer import tokenize
    from liminate.parser import parse
    from liminate.renderer import render

    tokens = tokenize("remember a list called items")
    ast = parse(tokens)
    assert render(ast) == "remember a list called items"


# ---------------------------------------------------------------------------
# Sentinel clearing (none-seeded list)
# ---------------------------------------------------------------------------


def test_el6_none_seed_cleared_on_first_add():
    """First add to a `none`-seeded list clears the sentinel."""
    session, results = run_v3a(
        """
        remember a list called items with "none"
        add "a" to items
        """
    )
    errors = [r for r in results if r.status is not ResultStatus.SUCCESS]
    assert not errors, errors
    assert session.symtab["items"].value == ["a"]


def test_el7_none_seed_multiple_adds():
    """Multiple adds after a `none` seed produce a clean list."""
    session, results = run_v3a(
        """
        remember a list called items with "none"
        add "a" to items
        add "b" to items
        """
    )
    errors = [r for r in results if r.status is not ResultStatus.SUCCESS]
    assert not errors, errors
    assert session.symtab["items"].value == ["a", "b"]


def test_el10_show_after_adds_has_no_none_prefix():
    """show output after adds does not include the none sentinel."""
    _, results = run_v3a(
        """
        remember a list called items with "none"
        add "first" to items
        add "second" to items
        show items
        """
    )
    out = outputs(results)
    assert out == ["first, second"]
    assert "none" not in out[0]

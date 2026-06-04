"""Tests for D-3: empty list construction.

`remember a list called X` with no `with` clause produces an empty list,
gated on the `list` descriptor. Covers the build-prompt acceptance criteria.
(See also tests/test_integration_empty_list.py for the addendum-v4 suite.)
"""

from __future__ import annotations

from liminate.lexer import tokenize
from liminate.parser import RememberListNode, parse
from liminate.renderer import render
from liminate.result import ResultStatus

from tests._v3a_helpers import outputs, run_v3a


def test_empty_list_stored():
    session, results = run_v3a("remember a list called items")
    errors = [r for r in results if r.status is not ResultStatus.SUCCESS]
    assert not errors, errors
    assert session.symtab["items"].value == []


def test_add_then_count_is_one():
    session, results = run_v3a(
        """
        remember a list called items
        add 5 to items
        count items
        """
    )
    errors = [r for r in results if r.status is not ResultStatus.SUCCESS]
    assert not errors, errors
    assert session.symtab["items"].value == [5]
    assert outputs(results)[-1] == "1"


def test_show_empty_list_is_clean():
    _, results = run_v3a(
        """
        remember a list called items
        show items
        """
    )
    successes = [r for r in results if r.status is ResultStatus.SUCCESS]
    assert len(successes) == 2


def test_canonical_render_has_no_with():
    ast = parse(tokenize("remember a list called items"))
    assert isinstance(ast, RememberListNode)
    assert ast.items == []
    assert render(ast) == "remember a list called items"


def test_value_descriptor_without_with_is_parse_error():
    _, results = run_v3a("remember a value called items")
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results


def test_empty_form_gated_on_list_descriptor():
    # No descriptor at all (and no `with`) is still a parse error.
    _, results = run_v3a("remember a thing called items")
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results

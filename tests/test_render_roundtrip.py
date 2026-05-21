"""Regression tests for issue #18 — renderer round-trip fidelity for
`remember` value statements.

The renderer must emit the keyword the parser will re-parse to the SAME
*kind* of value:

  - literals (number, bare string, quoted string) -> `with`
  - copy references / computed expressions         -> `from`

Bug #18: a quoted-string literal was routed through `from`. Combined with
v2c conditional quoting (which drops the quotes around a safe single word),
`remember a string called alarm with "off"` rendered as
`remember a string called alarm from off` — which re-parses as a copy from
a variable named `off` (`NameRef`, via `_name_ref_for_from`), changing the
statement's meaning and crashing at runtime (`I can't find 'off'`).

Note on the assertion level: a strict `parse(render(x)) == x` cannot guard
this. v2c conditional quoting intentionally normalizes a quoted single-word
string to a bare word (`"off"` -> `off`), so `QuotedString` and `BareWord`
are interchangeable for safe single words — strict AST equality is too
strong. And a multi-word quoted string round-tripped even *with* the bug
(it kept its quotes, so `from "in progress"` still re-parsed to a
`QuotedString`), so it wouldn't catch the regression either. The load-
bearing invariant is therefore semantic: a literal must re-parse as a
literal (never a reference), and the program must execute identically.
"""

import io

import pytest

from liminate.cli import run_file
from liminate.lexer import tokenize
from liminate.parser import (
    ArithmeticNode,
    BareWord,
    NameRef,
    NumberLiteral,
    QuotedString,
    RememberValueNode,
    parse,
)
from liminate.renderer import render


def _remember(src):
    node = parse(tokenize(src))
    assert isinstance(node, RememberValueNode), f"{src!r} -> {node}"
    return node


def _string_of(value):
    if isinstance(value, QuotedString):
        return value.content
    if isinstance(value, BareWord):
        return value.word
    return None


# Every one of these is a *literal* value — it must render through `with`
# and re-parse as a literal, never a copy reference.
LITERAL_REMEMBERS = [
    'remember a string called alarm with "off"',       # the issue #18 repro
    'remember a string called s with "hello"',
    'remember a string called s with "in progress"',   # multi-word quoted
    "remember a string called s with active",          # bare word
    "remember a value called n with 5",
    "remember a value called n with 3.5",
]


@pytest.mark.parametrize("src", LITERAL_REMEMBERS)
def test_literal_value_renders_through_with(src):
    rendered = render(_remember(src))
    assert " with " in rendered, rendered
    assert " from " not in rendered, (
        f"literal value rendered through `from` (issue #18): {rendered!r}"
    )


@pytest.mark.parametrize("src", LITERAL_REMEMBERS)
def test_literal_value_reparses_as_literal_not_reference(src):
    node = _remember(src)
    rendered = render(node)
    reparsed = _remember(rendered)
    assert not isinstance(reparsed.value, NameRef), (
        f"{src!r} rendered to {rendered!r}, which re-parsed as a copy "
        f"reference (NameRef) instead of a literal — issue #18"
    )
    assert isinstance(reparsed.value, (NumberLiteral, BareWord, QuotedString))


def test_issue_18_exact_reproducer_preserves_string_value():
    node = _remember('remember a string called alarm with "off"')
    assert isinstance(node.value, QuotedString)
    assert node.value.content == "off"
    reparsed = _remember(render(node))
    # The value class may normalize (QuotedString <-> BareWord per v2c), but
    # it must stay a string literal carrying the same content — not a NameRef.
    assert _string_of(reparsed.value) == "off"


def test_copy_reference_still_renders_through_from():
    node = _remember("remember a value called y from x")
    assert isinstance(node.value, NameRef)
    rendered = render(node)
    assert rendered == "remember a value called y from x"
    assert isinstance(_remember(rendered).value, NameRef)


def test_arithmetic_value_still_renders_through_from():
    node = _remember("remember a value called total from price plus tax")
    assert isinstance(node.value, ArithmeticNode)
    reparsed = _remember(render(node))
    assert isinstance(reparsed.value, ArithmeticNode)
    # Operands stay references, not string literals.
    assert isinstance(reparsed.value.left, NameRef)
    assert isinstance(reparsed.value.right, NameRef)


@pytest.mark.parametrize("src", LITERAL_REMEMBERS)
def test_render_is_stable(src):
    # Rendering the rendered form yields the same string (fixpoint).
    once = render(_remember(src))
    twice = render(_remember(once))
    assert once == twice


def _run(tmp_path, src):
    p = tmp_path / "p.limn"
    p.write_text(src, encoding="utf-8")
    out = io.StringIO()
    run_file(str(p), out=out, quiet=True)
    return out.getvalue()


def test_issue_18_rendered_program_runs_identically(tmp_path):
    original_src = 'remember a string called alarm with "off"\nshow alarm\n'
    head = _remember(original_src.splitlines()[0])
    rendered_src = render(head) + "\nshow alarm\n"

    original_out = _run(tmp_path, original_src)
    rendered_out = _run(tmp_path, rendered_src)

    assert "Error" not in rendered_out, rendered_out
    assert original_out == rendered_out == "off\n"

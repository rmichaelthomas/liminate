"""Regression tests for issue #20 — `show each` inside an `each` body.

Iterating a scalar list and printing each element is a beginner's first
instinct (`each the nums show each`), but the parser hard-rejected the
`each` pronoun as a `show` target in every context. Bare `show` (target
None, "display the current iterator item", v1c §49) already worked inside
an `each` body; this wires the natural pronoun form to the same semantics.

Outside an `each` body there is no iterator, so `show each` is still an
error. The pronoun form canonicalizes to a bare `show` on render (both are
the same `ShowNode(target=None)`).
"""

import io

from liminate.cli import run_file
from liminate.lexer import tokenize
from liminate.parser import EachNode, ShowNode, parse
from liminate.renderer import render
from liminate.result import ResultStatus


def _run(tmp_path, src):
    p = tmp_path / "p.limn"
    p.write_text(src, encoding="utf-8")
    out = io.StringIO()
    run_file(str(p), out=out, quiet=True)
    return out.getvalue()


def test_show_each_parses_to_iterator_show():
    node = parse(tokenize("each the nums show each"))
    assert isinstance(node, EachNode)
    assert isinstance(node.action, ShowNode)
    # `show each` is the current-iterator-item show (target=None).
    assert node.action.target is None


def test_show_each_over_scalar_list(tmp_path):
    src = "gather the nums from 1 to 3\neach the nums show each\n"
    out = _run(tmp_path, src)
    assert "Error" not in out, out
    assert out.splitlines()[-3:] == ["1", "2", "3"]


def test_show_each_matches_bare_show(tmp_path):
    # The pronoun form and the bare form produce identical output.
    pronoun = _run(tmp_path, "gather the nums from 1 to 3\neach the nums show each\n")
    bare = _run(tmp_path, "gather the nums from 1 to 3\neach the nums show\n")
    assert pronoun == bare


def test_show_each_over_records_shows_whole_record(tmp_path):
    src = (
        "remember an order called o1 with total as 5\n"
        "remember a list called orders with o1\n"
        "each the orders show each\n"
    )
    out = _run(tmp_path, src)
    assert "Error" not in out, out
    assert "total: 5" in out


def test_show_each_outside_each_still_errors():
    result = parse(tokenize("show each"))
    assert result.status is ResultStatus.ERROR_PARSE
    assert "each" in result.message


def test_show_each_renders_canonically_as_bare_show():
    node = parse(tokenize("each the nums show each"))
    # The action canonicalizes to a bare `show` (same AST as a bare show).
    assert render(node.action) == "show"
    # Whole-statement render round-trips and stays stable.
    rendered = render(node)
    reparsed = parse(tokenize(rendered))
    assert isinstance(reparsed, EachNode)
    assert reparsed.action.target is None
    assert render(reparsed) == rendered

"""v25 vocabulary wave — `combine` -> `sum` rename + tombstone.

Covers the rename-specific behaviors that don't belong in the general
sum test coverage already migrated in test_parser.py / test_renderer.py /
test_analyzer.py / test_interpreter.py / test_integration.py /
test_lexer.py / test_reorderer.py / test_vocabulary.py: the tombstone
error, the reserved-word rejection, the empty-sum-is-0 additive-identity
guarantee, and the `_value_of_op` composition-return site.
"""

import pytest

from liminate.analyzer import SymbolEntry
from liminate.interpreter import execute
from liminate.lexer import tokenize
from liminate.parser import parse
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus
from liminate.vocabulary import TOMBSTONES


def run(line: str, symtab: dict[str, SymbolEntry] | None = None) -> LiminateResult:
    """Full pipeline: lex -> reorder -> parse -> execute. Deliberately not
    just parse() — failure mode #3 (reorderer mangling) only surfaces
    through the full CLI-equivalent path."""
    if symtab is None:
        symtab = {}
    tokens = tokenize(line)
    reordered = reorder(tokens)
    if isinstance(reordered, LiminateResult):
        return reordered
    comp_names = {n for n, e in symtab.items() if e.type == "composition"}
    ast = parse(reordered, composition_names=comp_names)
    if isinstance(ast, LiminateResult):
        return ast
    return execute(ast, symtab)


def test_sum_the_numbers_shows_int_preserving_total():
    symtab = {}
    run("gather the numbers from 1 to 5", symtab)
    r = run("sum the numbers", symtab)
    assert r.output == ["15"]
    assert symtab["numbers"].value == [1, 2, 3, 4, 5]


def test_remember_from_sum_captures():
    symtab = {}
    run("gather the numbers from 1 to 5", symtab)
    r = run("remember the result called total from sum the numbers", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert symtab["total"].value == 15


def test_composition_returning_sum_value():
    # Exercises _value_of_op's SumNode branch: a composition whose last
    # (and only) operation is `sum` returns that value to the caller.
    symtab = {}
    run("gather the numbers from 1 to 5", symtab)
    run("remember how to total-it: sum the numbers", symtab)
    r = run("remember a copy called grand-total from total-it", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert symtab["grand-total"].value == 15


def test_sum_of_empty_list_is_zero():
    symtab = {}
    run("remember a list called nums with 1", symtab)
    run("remove 1 from nums", symtab)
    assert symtab["nums"].value == []
    r = run("sum the nums", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["0"]


def test_combine_verb_position_is_rename_error():
    r = run("combine the numbers")
    assert r.status is ResultStatus.ERROR_PARSE
    assert r.message == "The word 'combine' was renamed — use 'sum'."


def test_combine_is_tombstoned_in_vocabulary():
    assert TOMBSTONES == {"combine": "sum"}


def test_combine_in_name_position_is_reserved_renamed_word():
    r = run("remember a value called combine with 5")
    assert r.status is ResultStatus.ERROR_PARSE
    assert "reserved" in r.message
    assert "renamed word" in r.message


def test_combine_in_value_position_is_bare_word_data():
    # v25 §1.2 — an unquoted tombstone in value position is data, not an
    # error: it falls through to BareWord like any other bare word,
    # keeping the freeing path open (VW-Q6).
    r = run('remember a status called label with combine')
    assert r.status is ResultStatus.SUCCESS
    assert r.executed is not False

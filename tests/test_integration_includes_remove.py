"""Integration tests for the `includes` connective and `remove` verb.

`includes` is a list-membership connective usable in `when`/`unless`,
`where`, and `choose if` conditions. `remove` retracts an item from a
list (mirror of `add`).
"""

from __future__ import annotations

from liminate.cli import Session
from liminate.result import ResultStatus


def run_lines(lines):
    session = Session()
    results = [session.run_line(line) for line in lines]
    return session, results


# ---------------------------------------------------------------------------
# remove — happy path and behaviors
# ---------------------------------------------------------------------------


def test_remove_string_from_list_of_strings():
    session, results = run_lines([
        "remember a list called names with alice and bob and charlie",
        "remove bob from names",
        "show names",
    ])
    assert results[1].status is ResultStatus.SUCCESS, results[1].message
    assert results[1].output is None  # silent mutation
    assert session.symtab["names"].value == ["alice", "charlie"]
    assert results[2].output == ["alice, charlie"]


def test_remove_decreases_length_by_one():
    session, _ = run_lines([
        "remember a list called scores with 10 and 20 and 30",
        "remove 20 from scores",
    ])
    assert session.symtab["scores"].value == [10, 30]


def test_remove_missing_item_is_error():
    _, results = run_lines([
        "remember a list called names with alice and bob",
        "remove charlie from names",
    ])
    # Runtime errors surface as ERROR_SEMANTIC (status mapping mirrors
    # other interpreter-time failures like missing field access).
    assert results[1].status is ResultStatus.ERROR_SEMANTIC
    assert results[1].message == "I can't find 'charlie' in 'names'."


def test_remove_first_occurrence_only():
    session, _ = run_lines([
        "remember a list called tags with urgent and review and urgent",
        "remove urgent from tags",
    ])
    # First occurrence removed, second still present.
    assert session.symtab["tags"].value == ["review", "urgent"]


def test_remove_then_add_clean_replacement():
    session, _ = run_lines([
        "remember a list called decisions with none",
        "add use-flask to decisions",
        "add use-fastapi to decisions",
        "remove use-flask from decisions",
    ])
    assert session.symtab["decisions"].value == ["use-fastapi"]


def test_remove_from_non_list_is_error():
    _, results = run_lines([
        "remember a value called total with 100",
        "remove 5 from total",
    ])
    assert results[1].status is ResultStatus.ERROR_SEMANTIC
    assert results[1].message == (
        "I can only remove from a list. 'total' is a number."
    )


def test_remove_self_mutation_inside_each_is_error():
    _, results = run_lines([
        "remember a list called items with a and b and c",
        "each the items remove each from items",
    ])
    # Either analyzer rejects at parse/analyze, or runtime — either way
    # we should not get SUCCESS. Confirm it's an error.
    assert results[1].status is not ResultStatus.SUCCESS


# ---------------------------------------------------------------------------
# includes — list membership in `when` conditions (Phase 2 driving)
# ---------------------------------------------------------------------------


def test_includes_in_choose_if_taken_when_present():
    _, results = run_lines([
        "remember a list called tags with urgent and review",
        'choose if tags includes "urgent": show "yes" otherwise show "no"',
    ])
    assert results[1].status is ResultStatus.SUCCESS, results[1].message
    assert results[1].output == ["yes"]


def test_includes_in_choose_if_not_taken_when_absent():
    _, results = run_lines([
        "remember a list called tags with review",
        'choose if tags includes "urgent": show "yes" otherwise show "no"',
    ])
    assert results[1].output == ["no"]


def test_not_includes_in_choose_if():
    _, results = run_lines([
        "remember a list called tags with review",
        'choose if tags not includes "urgent": show "ok" otherwise show "skip"',
    ])
    assert results[1].output == ["ok"]


def test_includes_with_scalar_left_operand_is_false():
    # A non-list on the left of `includes` evaluates to false (not an
    # error) — `includes` is a list-membership probe.
    _, results = run_lines([
        "remember a value called name with alice",
        'choose if name includes "alice": show "yes" otherwise show "no"',
    ])
    assert results[1].status is ResultStatus.SUCCESS
    assert results[1].output == ["no"]


def test_includes_none_seed_then_add_clears_seed():
    # Before any `add`, the `none`-seeded list literally contains "none".
    _, results = run_lines([
        "remember a list called decisions with none",
        'choose if decisions includes "none": show "seed" otherwise show "real"',
    ])
    assert results[1].output == ["seed"]

    _, results2 = run_lines([
        "remember a list called decisions with none",
        "add use-fastapi to decisions",
        'choose if decisions includes "none": show "seed" otherwise show "real"',
    ])
    assert results2[2].output == ["real"]


# ---------------------------------------------------------------------------
# Round-trip rendering
# ---------------------------------------------------------------------------


def test_remove_renders_canonically():
    from liminate.lexer import tokenize
    from liminate.parser import parse
    from liminate.renderer import render

    # `use-flask` is a single bare word — conditional quoting (v2c §90)
    # drops the quotes on re-render because the value is single-token,
    # all-lowercase, and not a reserved word.
    tokens = tokenize('remove "use-flask" from the decisions')
    ast = parse(tokens)
    assert render(ast) == "remove use-flask from decisions"
    # And the rendered form round-trips through the parser.
    parse(tokenize(render(ast)))


def test_includes_renders_canonically():
    from liminate.lexer import tokenize
    from liminate.parser import parse
    from liminate.renderer import render

    tokens = tokenize('choose if tags includes "urgent": show "yes"')
    ast = parse(tokens)
    rendered = render(ast)
    assert "tags includes" in rendered
    # Round-trip: rendered form must re-parse.
    parse(tokenize(rendered))


def test_not_includes_renders_canonically():
    from liminate.lexer import tokenize
    from liminate.parser import parse
    from liminate.renderer import render

    tokens = tokenize('choose if tags not includes "urgent": show "yes"')
    ast = parse(tokens)
    rendered = render(ast)
    assert "tags not includes" in rendered
    parse(tokenize(rendered))


# ---------------------------------------------------------------------------
# Listener path — `when ... includes` fires during initial evaluation.
#
# Regression guard for the `_apply_op` duplication between interpreter.py
# and listener.py: when new operators are added to one copy they must
# also be added to the other, otherwise a `when` handler that parses and
# registers fine will raise "Unknown comparison operator" at firing time.
# ---------------------------------------------------------------------------


def _drain(iterable):
    return list(iterable)


def test_when_includes_fires_on_initial_evaluation():
    from liminate.adapter import LiveValueRegistry
    from liminate.analyzer import SymbolEntry
    from liminate.interpreter import HandlerTable, execute as _execute
    from liminate.lexer import tokenize
    from liminate.listener import listen
    from liminate.parser import parse_when_block
    from liminate.reorderer import reorder

    symtab: dict[str, SymbolEntry] = {}
    symtab["decisions"] = SymbolEntry(
        name="decisions",
        value=["use-fastapi"],
        type="list_of_strings",
    )
    ht = HandlerTable()
    reg = LiveValueRegistry()

    htoks = reorder(tokenize('when decisions includes "use-fastapi"'))
    atoks = [reorder(tokenize('show "Constraint active"'))]
    ast = parse_when_block(htoks, atoks)
    reg_result = _execute(ast, symtab, handler_table=ht, live_value_registry=reg)
    assert reg_result.status is ResultStatus.SUCCESS, reg_result.message

    results = _drain(listen(symtab, ht, reg, adapters=[]))
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    assert len(fires) == 1
    assert fires[0].output == ["Constraint active"]
    assert fires[0].metadata["trigger"]["source"] == "initial"


def test_when_not_includes_fires_on_initial_evaluation():
    from liminate.adapter import LiveValueRegistry
    from liminate.analyzer import SymbolEntry
    from liminate.interpreter import HandlerTable, execute as _execute
    from liminate.lexer import tokenize
    from liminate.listener import listen
    from liminate.parser import parse_when_block
    from liminate.reorderer import reorder

    symtab: dict[str, SymbolEntry] = {}
    symtab["decisions"] = SymbolEntry(
        name="decisions",
        value=["use-fastapi"],
        type="list_of_strings",
    )
    ht = HandlerTable()
    reg = LiveValueRegistry()

    htoks = reorder(tokenize('when decisions not includes "use-flask"'))
    atoks = [reorder(tokenize('show "flask not active"'))]
    ast = parse_when_block(htoks, atoks)
    reg_result = _execute(ast, symtab, handler_table=ht, live_value_registry=reg)
    assert reg_result.status is ResultStatus.SUCCESS, reg_result.message

    results = _drain(listen(symtab, ht, reg, adapters=[]))
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    assert len(fires) == 1
    assert fires[0].output == ["flask not active"]

"""v8a §49 (EXP-Q1 resolution) — tests for the `require each` grammar
extension: iterated enforcement with a named binding.

    require each {name} in {list} {condition}

Covers parsing (the second parse shape, error paths, reserved-word
binding), analysis (collection-is-a-list, binding ≠ collection name),
execution (silent pass, REQUIREMENT_NOT_MET identifying the failing
element, scalar and record lists, compound conditions, empty lists,
binding hygiene), metadata modifiers (because / inherited / starting /
until), mixed-precedence amber, and regression guards for the unchanged
single-condition `require`, the `each` verb, and the `each` pronoun.
"""

from __future__ import annotations

from liminate.cli import Session
from liminate.lexer import tokenize
from liminate.parser import (
    CompoundConditionNode,
    ConditionNode,
    EachPronoun,
    NameRef,
    RequireEachNode,
    RequireNode,
    parse,
)
from liminate.renderer import render
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse(line: str):
    toks = tokenize(line)
    reordered = reorder(toks)
    if isinstance(reordered, LiminateResult):
        return reordered
    return parse(reordered)


def _session() -> Session:
    return Session()


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_parses_basic_scalar_list():
    ast = _parse("require each score in scores is above 70")
    assert isinstance(ast, RequireEachNode)
    assert ast.binding_name == "score"
    assert isinstance(ast.collection, NameRef)
    assert ast.collection.name == "scores"
    assert isinstance(ast.condition, ConditionNode)
    assert ast.condition.op == "above"
    # Field is elided → bound to the current element via EachPronoun.
    assert isinstance(ast.condition.field, EachPronoun)


def test_parses_basic_record_list():
    ast = _parse("require each hazard in machine-hazards is guarded")
    assert isinstance(ast, RequireEachNode)
    assert ast.binding_name == "hazard"
    assert ast.collection.name == "machine-hazards"
    assert isinstance(ast.condition, ConditionNode)


def test_parses_compound_condition_with_explicit_binding():
    ast = _parse(
        "require each item in items is above 5 and item is below 100"
    )
    assert isinstance(ast, RequireEachNode)
    assert isinstance(ast.condition, CompoundConditionNode)
    assert ast.condition.connector == "and"
    # First branch elides its field (EachPronoun); second names the binding.
    assert isinstance(ast.condition.left.field, EachPronoun)
    assert isinstance(ast.condition.right.field, NameRef)
    assert ast.condition.right.field.name == "item"


def test_parses_not_operator():
    ast = _parse('require each value in values is not equal to "invalid"')
    assert isinstance(ast, RequireEachNode)
    assert ast.condition.op == "not_equal_to"


def test_parses_includes_operator():
    ast = _parse('require each tag-list in all-tag-lists includes "required"')
    assert isinstance(ast, RequireEachNode)
    assert ast.condition.op == "includes"


def test_parses_within_operator():
    ast = _parse("require each reading in readings is within 5 of baseline")
    assert isinstance(ast, RequireEachNode)
    assert ast.condition.op == "within"


def test_error_missing_in():
    r = _parse("require each score scores is above 70")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE
    assert "in" in (r.message or "")


def test_error_missing_condition():
    r = _parse("require each score in scores")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE
    assert "condition" in (r.message or "")


def test_error_reserved_word_as_binding():
    r = _parse("require each filter in items is above 5")
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.ERROR_PARSE
    assert "reserved" in (r.message or "")


# ---------------------------------------------------------------------------
# Integration — scalar lists
# ---------------------------------------------------------------------------


def test_all_pass_scalar_list():
    s = _session()
    s.run_line("remember a list called scores with 80 and 90 and 75")
    r = s.run_line("require each score in scores is above 70")
    assert r.status is ResultStatus.SUCCESS
    assert r.output is None


def test_one_fails_scalar_list_identifies_element():
    s = _session()
    s.run_line("remember a list called scores with 80 and 60 and 75")
    r = s.run_line("require each score in scores is above 70")
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET
    assert "Requirement not met" in (r.message or "")
    assert "element 2" in (r.message or "")


# ---------------------------------------------------------------------------
# Integration — record lists
# ---------------------------------------------------------------------------


def _seed_records(s: Session, second_status: str) -> None:
    s.run_line("remember a record called alpha with name as a1 and status as active")
    s.run_line(
        f"remember a record called beta with name as b1 and status as {second_status}"
    )
    s.run_line("remember a list called items with alpha and beta")


def test_all_pass_record_list():
    s = _session()
    _seed_records(s, "active")
    r = s.run_line('require each item in items status is equal to "active"')
    assert r.status is ResultStatus.SUCCESS


def test_one_fails_record_list():
    s = _session()
    _seed_records(s, "inactive")
    r = s.run_line('require each item in items status is equal to "active"')
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET
    assert "element 2" in (r.message or "")


# ---------------------------------------------------------------------------
# Integration — compound conditions
# ---------------------------------------------------------------------------


def test_compound_all_pass():
    s = _session()
    s.run_line("remember a list called values with 5 and 50 and 99")
    r = s.run_line(
        "require each val in values is above 0 and val is below 100"
    )
    assert r.status is ResultStatus.SUCCESS


def test_compound_one_fails():
    s = _session()
    s.run_line("remember a list called values with 5 and 150 and 99")
    r = s.run_line(
        "require each val in values is above 0 and val is below 100"
    )
    assert r.status is ResultStatus.REQUIREMENT_NOT_MET
    assert "element 2" in (r.message or "")


# ---------------------------------------------------------------------------
# Integration — edge cases & binding hygiene
# ---------------------------------------------------------------------------


def test_empty_list_is_vacuously_true():
    s = _session()
    # Build an empty list by filtering everything out.
    s.run_line("remember a list called nums with 1 and 2 and 3")
    s.run_line("filter nums where each is above 100")
    r = s.run_line("require each item in nums is above 0")
    assert r.status is ResultStatus.SUCCESS


def test_binding_does_not_leak():
    s = _session()
    s.run_line("remember a list called scores with 80 and 90 and 75")
    r = s.run_line("require each score in scores is above 70")
    assert r.status is ResultStatus.SUCCESS
    assert "score" not in s.symtab


def test_binding_restores_shadowed_name():
    s = _session()
    s.run_line("remember a value called score with 999")
    s.run_line("remember a list called scores with 80 and 90 and 75")
    r = s.run_line("require each score in scores is above 70")
    assert r.status is ResultStatus.SUCCESS
    assert s.symtab["score"].value == 999


def test_error_binding_name_equals_collection_name():
    s = _session()
    s.run_line("remember a list called scores with 80 and 90")
    r = s.run_line("require each scores in scores is above 70")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "same as the list name" in (r.message or "")


def test_works_inside_then_sequence():
    s = _session()
    r = s.run_line(
        "remember a list called nums with 1 and 2 and 3 "
        "then require each n in nums is above 0"
    )
    assert r.status is ResultStatus.SUCCESS


# ---------------------------------------------------------------------------
# Metadata modifiers
# ---------------------------------------------------------------------------


def test_because_rationale_preserved():
    ast = _parse(
        'require each score in scores is above 70 '
        'because "minimum passing grade"'
    )
    assert isinstance(ast, RequireEachNode)
    assert ast.rationale == "minimum passing grade"
    assert 'because "minimum passing grade"' in render(ast)


def test_inherited_modifier():
    ast = _parse("inherited require each score in scores is above 70")
    assert isinstance(ast, RequireEachNode)
    assert ast.inherited is True
    assert render(ast).startswith("inherited ")


def test_starting_until_modifiers():
    ast = _parse(
        'starting "2025-07-01" until "2025-12-31" '
        "require each score in scores is above 70"
    )
    assert isinstance(ast, RequireEachNode)
    assert ast.starting_date == "2025-07-01"
    assert ast.until_date == "2025-12-31"


def test_mixed_and_or_triggers_amber():
    r = _parse(
        "require each item in items is above 5 and item is below 100 "
        "or item is equal to 0"
    )
    assert isinstance(r, LiminateResult)
    assert r.status is ResultStatus.AMBER_PRECEDENCE


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_render_round_trip_is_stable():
    ast = _parse("require each score in scores is above 70")
    canonical = render(ast)
    again = _parse(canonical)
    assert isinstance(again, RequireEachNode)
    assert render(again) == canonical


def test_render_round_trip_compound():
    ast = _parse(
        "require each item in items is above 5 and item is below 100"
    )
    canonical = render(ast)
    again = _parse(canonical)
    assert isinstance(again, RequireEachNode)
    assert render(again) == canonical


# ---------------------------------------------------------------------------
# Regression guards (§8 invariants 2 & 3)
# ---------------------------------------------------------------------------


def test_existing_require_unchanged():
    ast = _parse("require total is above 100")
    assert isinstance(ast, RequireNode)
    assert not isinstance(ast, RequireEachNode)
    assert ast.condition.op == "above"


def test_each_standalone_verb_unchanged():
    s = _session()
    s.run_line("remember a list called scores with 1 and 2")
    r = s.run_line("each scores show")
    assert r.status is ResultStatus.SUCCESS


def test_each_pronoun_in_where_unchanged():
    s = _session()
    s.run_line("remember a list called scores with 40 and 60")
    r = s.run_line("filter the scores where each is above 50")
    assert r.status is ResultStatus.SUCCESS

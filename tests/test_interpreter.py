"""Phase 6 gate tests: interpreter (§24, v1b §38-§42, v1c §49, v1d §56-§64)."""

import pytest

from inscript.analyzer import SymbolEntry
from inscript.interpreter import execute
from inscript.lexer import tokenize
from inscript.parser import parse
from inscript.reorderer import reorder
from inscript.result import InscriptResult, ResultStatus


# ---------------------------------------------------------------------------
# Helpers — running one statement against a shared symbol table
# ---------------------------------------------------------------------------


def run(line: str, symtab: dict[str, SymbolEntry] | None = None) -> InscriptResult:
    if symtab is None:
        symtab = {}
    tokens = tokenize(line)
    if not tokens:
        return InscriptResult(status=ResultStatus.SUCCESS, output=None, executed=True)
    reordered = reorder(tokens)
    if isinstance(reordered, InscriptResult):
        return reordered
    comp_names = {n for n, e in symtab.items() if e.type == "composition"}
    ast = parse(reordered, composition_names=comp_names)
    if isinstance(ast, InscriptResult):
        return ast
    return execute(ast, symtab)


def run_program(lines: list[str]) -> tuple[dict[str, SymbolEntry], list[InscriptResult]]:
    symtab: dict[str, SymbolEntry] = {}
    results = [run(line, symtab) for line in lines]
    return symtab, results


# ---------------------------------------------------------------------------
# remember + show (Program 1)
# ---------------------------------------------------------------------------


def test_remember_number_stores_silently():
    symtab: dict[str, SymbolEntry] = {}
    r = run("remember a number called age with 30", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert r.output is None
    assert symtab["age"].value == 30
    assert symtab["age"].type == "number"


def test_show_number():
    symtab = {}
    run("remember a number called age with 30", symtab)
    r = run("show age", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["30"]


def test_remember_list_of_strings():
    symtab = {}
    run("remember a list called colors with red and blue and green", symtab)
    assert symtab["colors"].value == ["red", "blue", "green"]
    assert symtab["colors"].type == "list_of_strings"


def test_show_list_of_strings_is_comma_separated():
    symtab = {}
    run("remember a list called colors with red and blue and green", symtab)
    r = run("show colors", symtab)
    assert r.output == ["red, blue, green"]


def test_count_auto_shows():
    symtab = {}
    run("remember a list called colors with red and blue and green", symtab)
    r = run("count the colors", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["3"]


# ---------------------------------------------------------------------------
# remember a record + show + each (Program 2)
# ---------------------------------------------------------------------------


def test_remember_record_stores_dict_with_schema():
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    assert symtab["order1"].value == {"total": 75, "status": "active"}
    assert symtab["order1"].schema == {"total": "number", "status": "string"}


def test_remember_list_of_records_copies_each_record():
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    run("remember an order called order2 with total as 30 and status as active", symtab)
    run("remember a list called orders with order1 and order2", symtab)
    assert symtab["orders"].type == "list_of_records"
    assert len(symtab["orders"].value) == 2
    # Copy semantics: mutating order1 should not affect orders[0] (§24 line 486).
    symtab["order1"].value["total"] = 999
    assert symtab["orders"].value[0]["total"] == 75


def test_each_show_field_emits_one_line_per_record():
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    run("remember an order called order2 with total as 30 and status as active", symtab)
    run("remember an order called order3 with total as 120 and status as pending", symtab)
    run("remember a list called orders with order1 and order2 and order3", symtab)
    r = run("each the orders show total", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["75", "30", "120"]


# ---------------------------------------------------------------------------
# filter is in-place (§24 line 478)
# ---------------------------------------------------------------------------


def test_filter_modifies_target_in_place():
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    run("remember an order called order2 with total as 30 and status as active", symtab)
    run("remember an order called order3 with total as 120 and status as pending", symtab)
    run("remember a list called orders with order1 and order2 and order3", symtab)
    r = run("filter the orders where total is above 50", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert r.output is None
    totals = [item["total"] for item in symtab["orders"].value]
    assert totals == [75, 120]


def test_filter_chain_reduces_records():
    symtab = {}
    for setup in [
        "remember an order called order1 with total as 75 and status as active",
        "remember an order called order2 with total as 30 and status as active",
        "remember an order called order3 with total as 120 and status as pending",
        "remember a list called orders with order1 and order2 and order3",
        "filter the orders where total is above 50",
        "filter the orders where status is active",
    ]:
        run(setup, symtab)
    assert len(symtab["orders"].value) == 1
    assert symtab["orders"].value[0]["total"] == 75


# ---------------------------------------------------------------------------
# keep — non-destructive filter (v2a §67)
# ---------------------------------------------------------------------------


def _seed_orders(symtab: dict[str, SymbolEntry]) -> None:
    run("remember an order called order1 with total as 75 and status as active", symtab)
    run("remember an order called order2 with total as 30 and status as active", symtab)
    run("remember an order called order3 with total as 120 and status as pending", symtab)
    run("remember a list called orders with order1 and order2 and order3", symtab)


def test_keep_auto_shows_matches_and_does_not_modify_source():
    symtab = {}
    _seed_orders(symtab)
    r = run("keep the orders where total is above 50", symtab)
    assert r.status is ResultStatus.SUCCESS
    # Auto-show output present for the two matching records.
    assert r.output is not None and len(r.output) == 2
    assert "total: 75" in r.output[0]
    assert "total: 120" in r.output[1]
    # Source list is unchanged — D3 dissolves because compositions
    # wrapping `keep` can be called repeatedly on the same data.
    totals = [item["total"] for item in symtab["orders"].value]
    assert totals == [75, 30, 120]


def test_keep_empty_result_does_not_modify_source():
    symtab = {}
    _seed_orders(symtab)
    r = run("keep the orders where total is above 999", symtab)
    assert r.status is ResultStatus.SUCCESS
    # No matches → empty list auto-shown as an empty line.
    assert r.output == [""]
    # Source preserved.
    assert len(symtab["orders"].value) == 3


def test_keep_captured_via_remember_from():
    symtab = {}
    _seed_orders(symtab)
    r = run(
        "remember the matches called big from keep the orders where total is above 50",
        symtab,
    )
    assert r.status is ResultStatus.SUCCESS
    # Source untouched.
    assert len(symtab["orders"].value) == 3
    # Captured list contains the 2 matching records.
    assert symtab["big"].type == "list_of_records"
    assert len(symtab["big"].value) == 2
    assert [r["total"] for r in symtab["big"].value] == [75, 120]


def test_keep_compound_condition():
    symtab = {}
    _seed_orders(symtab)
    r = run(
        "keep the orders where total is above 50 and status is active",
        symtab,
    )
    assert r.status is ResultStatus.SUCCESS
    # Only order1 (75/active) matches both.
    assert r.output is not None and len(r.output) == 1
    assert "total: 75" in r.output[0]
    # Source still 3.
    assert len(symtab["orders"].value) == 3


def test_keep_in_composition_is_reusable():
    # v2a §67 / D3: a composition wrapping `keep` can be called repeatedly
    # because the source list is never mutated. Same input → same output.
    symtab = {}
    _seed_orders(symtab)
    run("remember how to find-big: keep the orders where total is above 50", symtab)
    r1 = run("find-big", symtab)
    r2 = run("find-big", symtab)
    assert r1.status is ResultStatus.SUCCESS
    assert r2.status is ResultStatus.SUCCESS
    assert r1.output == r2.output  # idempotent
    assert len(symtab["orders"].value) == 3  # source preserved


def test_keep_on_scalar_is_semantic_error():
    symtab = {}
    run("remember a number called age with 30", symtab)
    r = run("keep the age where each is above 5", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "keep" in r.message
    assert "age" in r.message


# ---------------------------------------------------------------------------
# show <field> of <record> — single-record field access (v2a §68, D4)
# ---------------------------------------------------------------------------


def test_show_field_of_record_returns_field_value():
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    r = run("show total of order1", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["75"]


def test_show_string_field_of_record():
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    r = run("show status of order1", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["active"]


def test_show_field_of_record_missing_field_is_semantic_error():
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    r = run("show missing of order1", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "order1" in r.message
    assert "missing" in r.message


def test_show_field_of_missing_record_is_semantic_error():
    symtab = {}
    r = run("show total of ghost", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "ghost" in r.message


def test_show_field_of_non_record_is_semantic_error():
    symtab = {}
    run("remember a number called age with 30", symtab)
    r = run("show something of age", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "age" in r.message
    # The error explains that `of` needs a record.
    assert "of" in r.message.lower() or "record" in r.message.lower()


# ---------------------------------------------------------------------------
# each ... show <a> and <b>: multi-field display (v2a §69, D1)
# ---------------------------------------------------------------------------


def _seed_docs(symtab: dict[str, SymbolEntry]) -> None:
    run("remember a doc called d1 with class as checkpoint and words as 1000", symtab)
    run("remember a doc called d2 with class as addendum and words as 2000", symtab)
    run("remember a list called docs with d1 and d2", symtab)


def test_each_show_multiple_fields_emits_field_value_pairs():
    symtab = {}
    _seed_docs(symtab)
    r = run("each the docs show words and class", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert r.output == [
        "words: 1000, class: checkpoint",
        "words: 2000, class: addendum",
    ]


def test_each_show_single_field_still_emits_bare_value():
    # v2a §69 must not regress the existing single-field behavior.
    symtab = {}
    _seed_docs(symtab)
    r = run("each the docs show words", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["1000", "2000"]


def test_each_show_three_fields():
    # Field names avoid single-letter clashes with reserved words
    # (`a`/`an`/`to` are reserved; `x`/`y`/`z` are not).
    symtab = {}
    run("remember a rec called r1 with x as 1 and y as 2 and z as 3", symtab)
    run("remember a rec called r2 with x as 10 and y as 20 and z as 30", symtab)
    run("remember a list called records with r1 and r2", symtab)
    r = run("each the records show x and y and z", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert r.output == [
        "x: 1, y: 2, z: 3",
        "x: 10, y: 20, z: 30",
    ]


def test_each_show_unknown_field_is_semantic_error():
    symtab = {}
    _seed_docs(symtab)
    r = run("each the docs show words and nonexistent", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "nonexistent" in r.message


def test_show_and_field_outside_each_is_semantic_error():
    # v2a §69: multi-field `show` is only valid inside `each`. Outside,
    # `and` after `show <name>` is interpreted as operation sequencing,
    # which fails when followed by an unknown rather than a verb.
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    r = run("show total and status of order1", symtab)
    # Either parse error or semantic error is acceptable — the construct
    # is rejected.
    assert r.status in (ResultStatus.ERROR_PARSE, ResultStatus.ERROR_SEMANTIC)


# ---------------------------------------------------------------------------
# gather both stores and auto-shows (v1b §40)
# ---------------------------------------------------------------------------


def test_gather_stores_and_auto_shows():
    symtab = {}
    r = run("gather the numbers from 1 to 10", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["1, 2, 3, 4, 5, 6, 7, 8, 9, 10"]
    assert symtab["numbers"].value == list(range(1, 11))
    assert symtab["numbers"].type == "list_of_numbers"


def test_gather_equal_endpoints_single_item():
    symtab = {}
    run("gather the numbers from 5 to 5", symtab)
    assert symtab["numbers"].value == [5]


# ---------------------------------------------------------------------------
# combine non-destructive (v1b §39)
# ---------------------------------------------------------------------------


def test_combine_returns_sum_and_does_not_modify_source():
    symtab = {}
    run("gather the numbers from 1 to 5", symtab)
    r = run("combine the numbers", symtab)
    assert r.output == ["15"]
    assert symtab["numbers"].value == [1, 2, 3, 4, 5]  # unchanged


def test_remember_from_combine_captures_result():
    symtab = {}
    run("gather the numbers from 1 to 5", symtab)
    run("remember the result called total from combine the numbers", symtab)
    assert symtab["total"].value == 15
    assert symtab["total"].type == "number"
    # Source remains unchanged after capture.
    assert symtab["numbers"].value == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# `not` operator semantics (§21 line 416)
# ---------------------------------------------------------------------------


def test_not_above_includes_boundary():
    symtab = {}
    run("gather the scores from 1 to 10", symtab)
    run("filter the scores where each is not above 7", symtab)
    assert symtab["scores"].value == [1, 2, 3, 4, 5, 6, 7]


def test_not_below_includes_boundary():
    symtab = {}
    run("gather the scores from 1 to 10", symtab)
    run("filter the scores where each is not above 7", symtab)
    run("filter the scores where each is not below 3", symtab)
    assert symtab["scores"].value == [3, 4, 5, 6, 7]


def test_not_equal_to_removes_boundary():
    symtab = {}
    run("gather the scores from 1 to 10", symtab)
    run("filter the scores where each is not above 7", symtab)
    run("filter the scores where each is not below 3", symtab)
    run("filter the scores where each is not equal to 5", symtab)
    assert symtab["scores"].value == [3, 4, 6, 7]


# ---------------------------------------------------------------------------
# equal to (sentence 30)
# ---------------------------------------------------------------------------


def test_equal_to_filters_exactly():
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    run("remember an order called order2 with total as 30 and status as active", symtab)
    run("remember a list called orders with order1 and order2", symtab)
    run("filter the orders where total is equal to 75", symtab)
    assert len(symtab["orders"].value) == 1
    assert symtab["orders"].value[0]["total"] == 75


# ---------------------------------------------------------------------------
# Display formats (v1b §42)
# ---------------------------------------------------------------------------


def test_show_record_uses_field_value_pairs():
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    r = run("show order1", symtab)
    assert r.output == ["total: 75, status: active"]


def test_show_list_of_records_one_per_line():
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    run("remember an order called order2 with total as 30 and status as active", symtab)
    run("remember a list called orders with order1 and order2", symtab)
    r = run("show orders", symtab)
    assert r.output == [
        "total: 75, status: active",
        "total: 30, status: active",
    ]


# ---------------------------------------------------------------------------
# Sentence 40 — descriptor decorative, type inferred from value
# ---------------------------------------------------------------------------


def test_sentence_40_descriptor_ignored_value_is_string():
    symtab = {}
    run("remember a number called label with hello", symtab)
    assert symtab["label"].type == "string"
    assert symtab["label"].value == "hello"
    r = run("show label", symtab)
    assert r.output == ["hello"]


# ---------------------------------------------------------------------------
# Sentence 44 — duplicate name overwrite (v1d §58)
# ---------------------------------------------------------------------------


def test_duplicate_name_overwrites_silently():
    symtab = {}
    run("remember a number called age with 30", symtab)
    run("remember a number called age with 40", symtab)
    r = run("show age", symtab)
    assert r.output == ["40"]


def test_type_can_change_on_overwrite():
    symtab = {}
    run("remember a number called x with 30", symtab)
    run("remember a list called x with red and blue", symtab)
    assert symtab["x"].type == "list_of_strings"
    assert symtab["x"].value == ["red", "blue"]


# ---------------------------------------------------------------------------
# Sentence 46 — composition definition + call-time error
# ---------------------------------------------------------------------------


def test_composition_definition_succeeds_without_name_resolution():
    symtab = {}
    r = run("remember how to show-missing: show missingname", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert symtab["show-missing"].type == "composition"


def test_composition_call_runs_body_against_current_symtab():
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    run("remember an order called order2 with total as 30 and status as active", symtab)
    run("remember a list called orders with order1 and order2", symtab)
    run("remember how to find-big-orders: filter the orders where total is above 50", symtab)
    r = run("find-big-orders", symtab)
    assert r.status is ResultStatus.SUCCESS
    assert len(symtab["orders"].value) == 1
    assert symtab["orders"].value[0]["total"] == 75


def test_composition_call_errors_at_call_time_when_names_missing():
    symtab = {}
    run("remember how to show-missing: show missingname", symtab)
    r = run("show-missing", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "missingname" in r.message


# ---------------------------------------------------------------------------
# Sentence 47 — stepwise execution: earlier filter commits, later show fails
# ---------------------------------------------------------------------------


def test_stepwise_filter_commits_before_later_failure():
    symtab = {}
    run("remember a list called nums with 1 and 2 and 3 and 4 and 5", symtab)
    r = run("filter nums where each is above 3 and show missingname", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "missingname" in r.message
    # The filter side effect persisted (§56).
    assert symtab["nums"].value == [4, 5]
    # And the message acknowledges that.
    assert "filter has already been applied" in r.message


def test_show_after_stepwise_failure_sees_filtered_nums():
    symtab = {}
    run("remember a list called nums with 1 and 2 and 3 and 4 and 5", symtab)
    run("filter nums where each is above 3 and show missingname", symtab)
    r = run("show nums", symtab)
    assert r.output == ["4, 5"]


# ---------------------------------------------------------------------------
# Hostile semantic-error sentences from v1d §65
# ---------------------------------------------------------------------------


def test_sentence_35_show_missing_name():
    r = run("show missingname")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "missingname" in r.message


def test_sentence_36_filter_scalar():
    symtab = {}
    run("remember a number called age with 30", symtab)
    r = run("filter age where each is above 5", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "filter a list" in r.message


def test_sentence_37_combine_strings():
    symtab = {}
    run("remember a list called colors with red and blue and green", symtab)
    r = run("combine colors", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "only combine numbers" in r.message


def test_sentence_39_each_on_scalar():
    symtab = {}
    run("remember a number called age with 30", symtab)
    r = run("each the age show", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "iterate over a list" in r.message


def test_sentence_41_mixed_list():
    r = run("remember a list called mixed with 1 and blue")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "can't mix" in r.message


def test_sentence_42_descending_range():
    r = run("gather the numbers from 10 to 1")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "less than or equal" in r.message


def test_sentence_43_range_cap_exceeded():
    r = run("gather the numbers from 1 to 20000")
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert "10,000" in r.message


def test_sentence_48_schema_mismatch_in_list_of_records():
    symtab = {}
    run("remember an order called order1 with total as 75 and status as active", symtab)
    run("remember an item called item1 with price as 30 and color as red", symtab)
    run("remember a list called mixed-records with order1 and item1", symtab)
    r = run("filter the mixed-records where total is above 50", symtab)
    assert r.status is ResultStatus.ERROR_SEMANTIC
    # U2/U3: error names 'item1' as the offender (partial-match case).
    assert "'item1' in 'mixed-records'" in r.message
    assert "doesn't have a field called 'total'" in r.message
    assert "Other items do have it" in r.message


# ---------------------------------------------------------------------------
# Programs 1–5 end-to-end (the locked thirty)
# ---------------------------------------------------------------------------


def test_program_1_basics():
    symtab, results = run_program([
        "remember a number called age with 30",
        "remember a list called colors with red and blue and green",
        "show age",
        "show colors",
        "count the colors",
    ])
    assert results[2].output == ["30"]
    assert results[3].output == ["red, blue, green"]
    assert results[4].output == ["3"]


def test_program_2_records_and_each():
    symtab, results = run_program([
        "remember an order called order1 with total as 75 and status as active",
        "remember an order called order2 with total as 30 and status as active",
        "remember an order called order3 with total as 120 and status as pending",
        "remember a list called orders with order1 and order2 and order3",
        "each the orders show total",
    ])
    assert results[-1].output == ["75", "30", "120"]


def test_program_3_filter_records():
    symtab, results = run_program([
        "remember an order called order1 with total as 75 and status as active",
        "remember an order called order2 with total as 30 and status as active",
        "remember an order called order3 with total as 120 and status as pending",
        "remember a list called orders with order1 and order2 and order3",
        "filter the orders where total is above 50",
        "filter the orders where status is active",
        "count the orders",
        "each the orders show status",
    ])
    assert results[-2].output == ["1"]
    assert results[-1].output == ["active"]


def test_program_4_number_operations():
    symtab, results = run_program([
        "gather the numbers from 1 to 10",
        "filter the numbers where each is above 5",
        "count the numbers",
        "combine the numbers",
        "remember the result called total from combine the numbers",
    ])
    assert results[0].output == ["1, 2, 3, 4, 5, 6, 7, 8, 9, 10"]
    assert results[2].output == ["5"]
    assert results[3].output == ["40"]
    assert symtab["total"].value == 40
    # numbers unchanged after the capture (combine non-destructive)
    assert symtab["numbers"].value == [6, 7, 8, 9, 10]


def test_program_5_not_operator():
    symtab, results = run_program([
        "gather the scores from 1 to 10",
        "filter the scores where each is not above 7",
        "filter the scores where each is not below 3",
        "filter the scores where each is not equal to 5",
    ])
    assert symtab["scores"].value == [3, 4, 6, 7]


# ---------------------------------------------------------------------------
# Compound conditions (sentences 27-28)
# ---------------------------------------------------------------------------


def test_compound_and_filters_intersection():
    symtab = {}
    for s in [
        "remember an order called order1 with total as 75 and status as active",
        "remember an order called order2 with total as 30 and status as active",
        "remember an order called order3 with total as 120 and status as pending",
        "remember a list called orders with order1 and order2 and order3",
    ]:
        run(s, symtab)
    run("filter the orders where total is above 50 and status is active", symtab)
    assert len(symtab["orders"].value) == 1
    assert symtab["orders"].value[0]["total"] == 75


def test_compound_or_filters_union():
    symtab = {}
    for s in [
        "remember an order called order1 with total as 75 and status as active",
        "remember an order called order2 with total as 30 and status as active",
        "remember an order called order3 with total as 120 and status as pending",
        "remember a list called orders with order1 and order2 and order3",
    ]:
        run(s, symtab)
    run("filter the orders where total is below 30 or status is pending", symtab)
    # order3 has status=pending; nobody has total<30.
    statuses = [o["status"] for o in symtab["orders"].value]
    assert statuses == ["pending"]


# ---------------------------------------------------------------------------
# Mixed precedence still returns AMBER (not executed)
# ---------------------------------------------------------------------------


def test_mixed_precedence_is_amber_and_does_not_execute():
    symtab = {}
    for s in [
        "remember an order called order1 with total as 75 and status as active",
        "remember a list called orders with order1",
    ]:
        run(s, symtab)
    before = list(symtab["orders"].value)
    r = run(
        "filter the orders where total is above 50 and status is active or status is pending",
        symtab,
    )
    assert r.status is ResultStatus.AMBER_PRECEDENCE
    assert r.executed is False
    assert symtab["orders"].value == before  # unchanged


# ---------------------------------------------------------------------------
# v3a §108 / §117 — Phase 1 `when` registration + live-value activation
# ---------------------------------------------------------------------------


from inscript.adapter import LiveValueDeclaration, LiveValueRegistry
from inscript.interpreter import (
    HandlerTable,
    _extract_when_dependencies,
    execute as _execute,
)
from inscript.lexer import tokenize as _tokenize
from inscript.parser import parse as _parse_line, parse_when_block
from inscript.reorderer import reorder


def _parse_when_for_test(header: str, *actions: str):
    htoks = reorder(_tokenize(header))
    atoks = [reorder(_tokenize(a)) for a in actions]
    return parse_when_block(htoks, atoks)


def test_when_registers_into_handler_table():
    """v3a §108: a `when` statement registers a handler but does not
    execute the action block. The handler table holds the WhenNode."""
    symtab: dict[str, SymbolEntry] = {}
    run("remember a number called temperature with 50", symtab)
    ht = HandlerTable()
    when_ast = _parse_when_for_test(
        "when temperature is above 100",
        'show "high alert"',
    )
    result = _execute(
        when_ast, symtab,
        handler_table=ht,
        live_value_registry=LiveValueRegistry(),
    )
    assert result.status is ResultStatus.SUCCESS
    assert len(ht.handlers) == 1
    assert ht.handlers[0].index == 0
    # The action block was NOT executed — no output side effect.
    assert result.output is None


def test_when_registration_order_preserved():
    """v3a §115: handlers fire in registration order. The table records
    them in source order; subsequent registrations append."""
    symtab: dict[str, SymbolEntry] = {}
    run("remember a number called score with 0", symtab)
    run("remember a number called level with 0", symtab)
    ht = HandlerTable()
    for header in (
        "when score is above 0",
        "when level is above 0",
    ):
        when_ast = _parse_when_for_test(header, 'show "x"')
        _execute(
            when_ast, symtab,
            handler_table=ht,
            live_value_registry=LiveValueRegistry(),
        )
    assert [h.index for h in ht.handlers] == [0, 1]


def test_when_with_missing_name_in_condition_does_not_register():
    """v3a §108: registration-time validation rejects unresolved names."""
    ht = HandlerTable()
    when_ast = _parse_when_for_test(
        "when missingname is above 100",
        'show "x"',
    )
    result = _execute(
        when_ast, {},
        handler_table=ht,
        live_value_registry=LiveValueRegistry(),
    )
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert len(ht.handlers) == 0  # not registered


def test_when_without_handler_table_returns_semantic_error():
    """Calling execute() with a WhenNode but no handler_table is a
    programmer-facing error (Session always provides one)."""
    symtab: dict[str, SymbolEntry] = {}
    run("remember a number called temperature with 50", symtab)
    when_ast = _parse_when_for_test(
        "when temperature is above 100", 'show "alert"',
    )
    result = _execute(when_ast, symtab)  # no handler_table
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "listener-capable Session" in result.message


# ---------- Dependency extraction (v3a §108 dependency rule) ----------


def test_extract_dependencies_bare_name():
    when_ast = _parse_when_for_test(
        "when temperature is above 100", 'show "x"',
    )
    assert _extract_when_dependencies(when_ast) == frozenset({"temperature"})


def test_extract_dependencies_of_expression_uses_record_name():
    """v3a §108: `<field> of <record>` depends on the record, not the
    field. Updates to the record trigger re-evaluation."""
    when_ast = _parse_when_for_test(
        "when status of patient is equal to critical",
        'show "alert"',
    )
    # `patient` is the record; `status` is just a field reference.
    assert _extract_when_dependencies(when_ast) == frozenset({"patient"})


def test_extract_dependencies_collects_compound():
    """Compound and/or conditions collect dependencies from both sides."""
    when_ast = _parse_when_for_test(
        "when temperature is above 100 and humidity is above 80",
        'show "danger"',
    )
    assert _extract_when_dependencies(when_ast) == frozenset(
        {"temperature", "humidity"}
    )


def test_extract_dependencies_includes_unless_guard():
    """v3a §109: the `unless` guard's dependencies are watched too."""
    when_ast = _parse_when_for_test(
        "when temperature is above 100 unless silenced is equal to true",
        'show "alert"',
    )
    assert _extract_when_dependencies(when_ast) == frozenset(
        {"temperature", "silenced"}
    )


def test_handler_table_watching_names_deterministic():
    """The LISTENING marker (§122) needs a stable name order."""
    symtab: dict[str, SymbolEntry] = {}
    for n in ("temperature", "humidity", "score"):
        run(f"remember a number called {n} with 0", symtab)
    ht = HandlerTable()
    for header in (
        "when humidity is above 80",
        "when temperature is above 100",
        "when score is above 0",
    ):
        when_ast = _parse_when_for_test(header, 'show "x"')
        _execute(
            when_ast, symtab,
            handler_table=ht,
            live_value_registry=LiveValueRegistry(),
        )
    # First-encounter order across handlers' (sorted) dependency sets.
    assert ht.watching_names() == ["humidity", "temperature", "score"]


def test_handler_table_dependents_of_filters_by_name():
    symtab: dict[str, SymbolEntry] = {}
    run("remember a number called temperature with 0", symtab)
    run("remember a number called humidity with 0", symtab)
    ht = HandlerTable()
    for header in (
        "when temperature is above 100",
        "when humidity is above 80",
        "when temperature is above 50",
    ):
        when_ast = _parse_when_for_test(header, 'show "x"')
        _execute(
            when_ast, symtab,
            handler_table=ht,
            live_value_registry=LiveValueRegistry(),
        )
    # Two handlers depend on temperature, one on humidity.
    deps = ht.dependents_of("temperature")
    assert {h.index for h in deps} == {0, 2}
    deps = ht.dependents_of("humidity")
    assert {h.index for h in deps} == {1}


def test_handler_table_dependents_excludes_disabled():
    """v3a §120: disabled handlers don't show up in dependent lookups."""
    symtab: dict[str, SymbolEntry] = {}
    run("remember a number called temperature with 0", symtab)
    ht = HandlerTable()
    when_ast = _parse_when_for_test(
        "when temperature is above 100", 'show "x"',
    )
    _execute(
        when_ast, symtab,
        handler_table=ht,
        live_value_registry=LiveValueRegistry(),
    )
    ht.handlers[0].disabled = True
    assert ht.dependents_of("temperature") == []


# ---------- v3a §117 — Phase 1 remember of a live value activates the registry ----------


def test_phase1_remember_of_live_value_marks_active():
    """v3a §117: a Phase 1 `remember` on a declared live value
    transitions the registry from "unset" to "active"."""
    symtab: dict[str, SymbolEntry] = {}
    registry = LiveValueRegistry()
    registry.declare(
        LiveValueDeclaration("temperature", "number"), "test-pack",
    )
    assert registry.is_unset("temperature")

    ast = _parse_line(_tokenize("remember a number called temperature with 50"))
    result = _execute(
        ast, symtab,
        handler_table=HandlerTable(),
        live_value_registry=registry,
    )
    assert result.status is ResultStatus.SUCCESS
    assert not registry.is_unset("temperature")
    assert registry.entry("temperature").status == "active"


def test_phase1_remember_of_non_live_value_does_not_touch_registry():
    """Remembering a name that isn't declared as a live value leaves
    the registry alone — Phase 1 init is opt-in by declaration."""
    symtab: dict[str, SymbolEntry] = {}
    registry = LiveValueRegistry()
    registry.declare(
        LiveValueDeclaration("temperature", "number"), "test-pack",
    )
    ast = _parse_line(_tokenize("remember a number called other with 99"))
    _execute(
        ast, symtab,
        handler_table=HandlerTable(),
        live_value_registry=registry,
    )
    # Live value untouched.
    assert registry.is_unset("temperature")


def test_phase1_remember_list_of_live_value_marks_active():
    """v3a §117 applies to all three remember flavors (value, list, record)."""
    symtab: dict[str, SymbolEntry] = {}
    registry = LiveValueRegistry()
    registry.declare(
        LiveValueDeclaration("readings", "list_of_numbers"), "test-pack",
    )
    ast = _parse_line(_tokenize("remember a list called readings with 10 and 20"))
    _execute(
        ast, symtab,
        handler_table=HandlerTable(),
        live_value_registry=registry,
    )
    assert not registry.is_unset("readings")

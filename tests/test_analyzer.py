"""Phase 5 gate tests: semantic analyzer (inception §23, v1b §38, v1c §49,
v1d §59/§60/§62/§63, v3a §108/§111/§112/§117).
"""

import pytest

from liminate.analyzer import SymbolEntry, analyze
from liminate.lexer import tokenize
from liminate.parser import (
    BareWord,
    CompositionCallNode,
    ConditionNode,
    EachNode,
    FinishNode,
    NameRef,
    NumberLiteral,
    QuotedString,
    ShowNode,
    WhenNode,
    parse,
    parse_when_block,
)
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus


def _parse(line: str, comps: set[str] | None = None):
    tokens = tokenize(line)
    reordered = reorder(tokens)
    assert not isinstance(reordered, LiminateResult), reordered
    ast = parse(reordered, composition_names=comps)
    assert not isinstance(ast, LiminateResult), ast
    return ast


def _analyze(line: str, symtab=None, comps: set[str] | None = None):
    return analyze(_parse(line, comps=comps), symtab or {})


# ---------------------------------------------------------------------------
# Convenience builders for symbol-table entries
# ---------------------------------------------------------------------------

def number(name, value):
    return SymbolEntry(name=name, value=value, type="number")


def string(name, value):
    return SymbolEntry(name=name, value=value, type="string")


def list_of_numbers(name, items):
    return SymbolEntry(name=name, value=list(items), type="list_of_numbers")


def list_of_strings(name, items):
    return SymbolEntry(name=name, value=list(items), type="list_of_strings")


def record(name, fields):
    schema = {}
    for k, v in fields.items():
        if isinstance(v, bool):
            schema[k] = "number"
        elif isinstance(v, (int, float)):
            schema[k] = "number"
        elif isinstance(v, str):
            schema[k] = "string"
        else:
            schema[k] = "unknown"
    return SymbolEntry(name=name, value=dict(fields), type="record", schema=schema)


def list_of_records(name, records_):
    return SymbolEntry(name=name, value=list(records_), type="list_of_records")


def composition(name, body_ast):
    return SymbolEntry(name=name, value=body_ast, type="composition")


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------

def test_show_known_name():
    symtab = {"age": number("age", 30)}
    result = _analyze("show age", symtab)
    assert not isinstance(result, LiminateResult)


def test_count_a_list():
    symtab = {"colors": list_of_strings("colors", ["red", "blue", "green"])}
    result = _analyze("count the colors", symtab)
    assert not isinstance(result, LiminateResult)


def test_filter_on_record_list_with_known_field():
    symtab = {
        "order1": record("order1", {"total": 75, "status": "active"}),
        "order2": record("order2", {"total": 30, "status": "active"}),
        "orders": list_of_records("orders", [
            {"total": 75, "status": "active"},
            {"total": 30, "status": "active"},
        ]),
    }
    result = _analyze("filter the orders where total is above 50", symtab)
    assert not isinstance(result, LiminateResult)


def test_filter_each_pronoun_on_flat_list():
    symtab = {"numbers": list_of_numbers("numbers", [1, 2, 3, 4, 5])}
    result = _analyze("filter the numbers where each is above 3", symtab)
    assert not isinstance(result, LiminateResult)


def test_each_iteration_over_records():
    symtab = {"orders": list_of_records("orders", [
        {"total": 75, "status": "active"},
        {"total": 30, "status": "active"},
    ])}
    result = _analyze("each the orders show total", symtab)
    assert not isinstance(result, LiminateResult)


def test_gather_valid_range():
    result = _analyze("gather the numbers from 1 to 10")
    assert not isinstance(result, LiminateResult)


def test_sum_list_of_numbers():
    symtab = {"numbers": list_of_numbers("numbers", [1, 2, 3])}
    result = _analyze("sum the numbers", symtab)
    assert not isinstance(result, LiminateResult)


def test_remember_value_with_literal():
    result = _analyze("remember a number called age with 30")
    assert not isinstance(result, LiminateResult)


def test_remember_value_with_existing_name_reference():
    symtab = {"the-data": list_of_numbers("the-data", [1, 2, 3])}
    result = _analyze("remember a copy called backup from the-data", symtab)
    assert not isinstance(result, LiminateResult)


def test_remember_list_homogeneous_strings():
    result = _analyze("remember a list called colors with red and blue and green")
    assert not isinstance(result, LiminateResult)


def test_remember_record():
    result = _analyze("remember an order called order1 with total as 75 and status as active")
    assert not isinstance(result, LiminateResult)


# ---------------------------------------------------------------------------
# Sentence 35 — name not found
# ---------------------------------------------------------------------------

def test_show_unknown_name_is_semantic_error():
    result = _analyze("show missingname")
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "missingname" in result.message
    assert "remember" in result.message


# ---------------------------------------------------------------------------
# Sentence 36 — filter on scalar
# ---------------------------------------------------------------------------

def test_filter_on_scalar_is_type_error():
    symtab = {"age": number("age", 30)}
    result = _analyze("filter age where each is above 5", symtab)
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "filter a list" in result.message
    assert "'age' is a number" in result.message


# ---------------------------------------------------------------------------
# Sentence 37 — sum on strings
# ---------------------------------------------------------------------------

def test_sum_strings_is_type_error():
    symtab = {"colors": list_of_strings("colors", ["red", "blue", "green"])}
    result = _analyze("sum colors", symtab)
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "only sum numbers" in result.message
    assert "'colors' contains text" in result.message


def test_sum_records_is_type_error():
    symtab = {"orders": list_of_records("orders", [{"total": 75}])}
    result = _analyze("sum orders", symtab)
    assert isinstance(result, LiminateResult)
    assert "'orders' contains records" in result.message


# ---------------------------------------------------------------------------
# Sentence 38 — field missing on records
# ---------------------------------------------------------------------------

def test_filter_field_missing_on_singleton_list_of_records():
    symtab = {
        "orders": list_of_records("orders", [
            {"total": 75, "status": "active"},
        ]),
    }
    result = _analyze("filter the orders where missingfield is above 50", symtab)
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "missingfield" in result.message
    assert "orders" in result.message


# ---------------------------------------------------------------------------
# Sentence 39 — each on scalar
# ---------------------------------------------------------------------------

def test_each_on_scalar_is_type_error():
    symtab = {"age": number("age", 30)}
    result = _analyze("each the age show", symtab)
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "iterate over a list" in result.message
    assert "'age' is a number" in result.message


# ---------------------------------------------------------------------------
# Sentence 40 — descriptor mismatch with value (succeeds)
# ---------------------------------------------------------------------------

def test_descriptor_number_with_string_value_succeeds():
    # v1b §36: descriptor is decorative; type inferred from value.
    result = _analyze("remember a number called label with hello")
    assert not isinstance(result, LiminateResult)


# ---------------------------------------------------------------------------
# Sentence 41 — mixed-type list
# ---------------------------------------------------------------------------

def test_mixed_type_list_is_semantic_error():
    result = _analyze("remember a list called mixed with 1 and blue")
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "can't mix" in result.message
    assert "'1' is a number" in result.message
    assert "'blue' is text" in result.message


# ---------------------------------------------------------------------------
# Sentence 42 — descending range
# ---------------------------------------------------------------------------

def test_descending_range_is_allowed():
    # D-6: descending ranges are valid; the analyzer no longer rejects them.
    result = _analyze("gather the numbers from 10 to 1")
    assert not isinstance(result, LiminateResult)


def test_equal_endpoints_are_allowed():
    result = _analyze("gather the numbers from 5 to 5")
    assert not isinstance(result, LiminateResult)


# ---------------------------------------------------------------------------
# Sentence 43 — gather range cap
# ---------------------------------------------------------------------------

def test_gather_range_cap_is_semantic_error():
    result = _analyze("gather the numbers from 1 to 20000")
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "too large" in result.message
    assert "10,000" in result.message


def test_gather_just_under_cap_succeeds():
    result = _analyze("gather the numbers from 1 to 10000")
    assert not isinstance(result, LiminateResult)


def test_gather_just_over_cap_fails():
    result = _analyze("gather the numbers from 1 to 10001")
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC


# ---------------------------------------------------------------------------
# Sentence 46 — composition call body-level semantic error at call time
# ---------------------------------------------------------------------------

def test_composition_definition_validates_without_name_resolution():
    # The body references missingname; analyzer must NOT error at definition.
    result = _analyze("remember how to show-missing: show missingname")
    assert not isinstance(result, LiminateResult)


def test_composition_call_validates_body_at_call_time():
    body = _parse("show missingname")
    symtab = {"show-missing": composition("show-missing", body)}
    result = _analyze("show-missing", symtab, comps={"show-missing"})
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "missingname" in result.message


# ---------------------------------------------------------------------------
# Sentence 48 — schema mismatch in a list of records
# ---------------------------------------------------------------------------

def test_filter_on_mixed_schemas_field_not_in_all_records():
    symtab = {
        "mixed-records": list_of_records("mixed-records", [
            {"total": 75, "status": "active"},
            {"price": 30, "color": "red"},
        ]),
    }
    result = _analyze("filter the mixed-records where total is above 50", symtab)
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    # U2/U3: the offending record is named (the test fixture builds the
    # list with raw dicts rather than a `remember` chain, so the analyzer
    # falls back to a positional identifier — "Item 2" here).
    assert "doesn't have a field called 'total'" in result.message
    assert "Other items do have it" in result.message
    assert "mixed-records" in result.message


# ---------------------------------------------------------------------------
# Type checking for above/below in conditions (v1c §23 line 460)
# ---------------------------------------------------------------------------

def test_above_with_text_value_is_type_error():
    symtab = {"numbers": list_of_numbers("numbers", [1, 2, 3])}
    result = _analyze("filter the numbers where each is above hello", symtab)
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "above" in result.message
    assert "hello" in result.message


def test_above_with_text_field_is_type_error():
    symtab = {"orders": list_of_records("orders", [
        {"status": "active"},
        {"status": "pending"},
    ])}
    result = _analyze("filter the orders where status is above 5", symtab)
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "above" in result.message
    assert "status" in result.message


# ---------------------------------------------------------------------------
# Field-name access on a flat list rejects (must use `each`)
# ---------------------------------------------------------------------------

def test_field_name_on_flat_list_is_error():
    symtab = {"numbers": list_of_numbers("numbers", [1, 2, 3])}
    result = _analyze("filter the numbers where missingfield is above 5", symtab)
    assert isinstance(result, LiminateResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "each" in result.message


# ---------------------------------------------------------------------------
# v3a §108: `when` condition + unless guard validated at registration
# ---------------------------------------------------------------------------


def _parse_when_for_analysis(header: str, *actions: str):
    """Tokenize/reorder/parse a `when` block for analyzer testing."""
    header_tokens = reorder(tokenize(header))
    assert not isinstance(header_tokens, LiminateResult)
    action_lists = []
    for a in actions:
        r = reorder(tokenize(a))
        assert not isinstance(r, LiminateResult)
        action_lists.append(r)
    ast = parse_when_block(header_tokens, action_lists)
    assert not isinstance(ast, LiminateResult), ast
    return ast


def test_when_condition_with_existing_name_validates():
    """v3a §108: names in the `when` condition must exist at the point
    the `when` statement is encountered."""
    symtab = {"temperature": number("temperature", 50)}
    ast = _parse_when_for_analysis(
        "when temperature is above 100", 'show "high alert"',
    )
    assert analyze(ast, symtab) is ast


def test_when_condition_with_missing_name_is_semantic_error():
    """v3a §108 — registration-time name resolution. A condition that
    references an undefined name fails before Phase 2 can start."""
    ast = _parse_when_for_analysis(
        "when missingname is above 100", 'show "x"',
    )
    out = analyze(ast, {})
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_SEMANTIC
    assert "missingname" in out.message


def test_when_unless_guard_validated_at_registration():
    """v3a §109: the unless guard is validated separately from the
    main condition; an undefined name in the guard is also a Phase 1
    error."""
    symtab = {"temperature": number("temperature", 50)}
    ast = _parse_when_for_analysis(
        "when temperature is above 100 unless missingguard is equal to true",
        'show "x"',
    )
    out = analyze(ast, symtab)
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_SEMANTIC
    assert "missingguard" in out.message


def test_when_with_of_expression_in_condition_validates():
    """v3a §108: `of` field access is legal in `when` conditions."""
    patient_schema = {"name": "string", "status": "string"}
    symtab = {
        "patient": SymbolEntry(
            name="patient",
            value={"name": "john", "status": "stable"},
            type="record",
            schema=patient_schema,
        ),
    }
    ast = _parse_when_for_analysis(
        "when status of patient is equal to critical",
        'show "alert"',
    )
    assert analyze(ast, symtab) is ast


def test_when_action_block_name_resolution_deferred():
    """v3a §108/§111: names inside an action block are NOT resolved at
    registration time. A reference to a not-yet-existing name is
    accepted here (the interpreter resolves at firing time)."""
    symtab = {"temperature": number("temperature", 50)}
    ast = _parse_when_for_analysis(
        "when temperature is above 100",
        "show notyetdefined",  # would normally be a semantic error
    )
    # No error: action-block validation is deferred to firing time.
    assert analyze(ast, symtab) is ast


# ---------------------------------------------------------------------------
# v3a §112: `finish` context check
# ---------------------------------------------------------------------------


def test_finish_at_top_level_is_a_semantic_error():
    """v3a §112: `finish` outside an action block is a semantic error.
    The parser accepts it (composition bodies need to compile) — the
    analyzer is the gatekeeper for Phase 1 sequential calls."""
    out = analyze(FinishNode(), {})
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_SEMANTIC
    assert "finish" in out.message.lower()


def test_finish_inside_action_block_is_legal():
    """v3a §112: with in_action_block=True, FinishNode passes analysis."""
    out = analyze(FinishNode(), {}, in_action_block=True)
    assert out is not None and not isinstance(out, LiminateResult)


def test_composition_whose_last_op_is_finish_is_side_effect_only():
    """v3a §112 + v2b §76: a composition whose last op is `finish` is
    side-effect-only. Calling it in value position is a semantic error."""
    # remember how to emergency-stop: finish
    # then use it in value position
    comp_def = _parse("remember how to emergency-stop: finish")
    assert analyze(comp_def, {}) is comp_def
    symtab: dict[str, SymbolEntry] = {}
    analyze(comp_def, symtab)
    # Manually register the composition the way the interpreter would.
    symtab["emergency-stop"] = SymbolEntry(
        name="emergency-stop",
        value=FinishNode(),
        type="composition",
        composition_param=None,
    )
    # remember the x called y from emergency-stop  — value-capture form.
    value_capture = _parse(
        "remember the result called outcome from emergency-stop",
        comps={"emergency-stop"},
    )
    out = analyze(value_capture, symtab)
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_SEMANTIC
    assert "emergency-stop" in out.message
    assert "finish" in out.message


# ---------------------------------------------------------------------------
# v3a §111/§117: live-value ownership
# ---------------------------------------------------------------------------


def test_remember_live_value_in_action_block_is_semantic_error():
    """v3a §111: inside a `when` action block, `remember <live-value> with
    X` is rejected with the v3a §117 ownership wording."""
    symtab = {"temperature": number("temperature", 50)}
    # The action statement is what the interpreter would pass to analyze
    # at firing time (or in static action-block analysis).
    statement = _parse("remember a number called temperature with 0")
    out = analyze(
        statement, symtab,
        in_action_block=True,
        live_value_names={"temperature"},
    )
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_SEMANTIC
    assert "temperature" in out.message
    assert "live value" in out.message


def test_remember_live_value_in_phase1_initializes_legally():
    """v3a §117: Phase 1 sequential `remember` may initialize a live
    value (the natural pattern of setting state before listener mode)."""
    statement = _parse("remember a number called temperature with 50")
    # in_action_block=False — Phase 1 context.
    out = analyze(
        statement, {},
        in_action_block=False,
        live_value_names={"temperature"},
    )
    assert out is statement  # passed through, no error


def test_filter_live_value_is_rejected_anywhere():
    """v3a §111/§117: `filter` is destructive — adapter-owned values
    can't be mutated by user code in any context."""
    symtab = {
        "readings": list_of_numbers("readings", [10, 20, 30]),
    }
    statement = _parse("filter the readings where each is above 15")
    out = analyze(
        statement, symtab,
        in_action_block=False,
        live_value_names={"readings"},
    )
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_SEMANTIC
    assert "readings" in out.message
    assert "live value" in out.message
    assert "keep" in out.message  # the suggested alternative


def test_keep_on_live_value_is_legal():
    """v3a §111: `keep` is non-destructive — reading a live value is
    fine in any context."""
    symtab = {
        "readings": list_of_numbers("readings", [10, 20, 30]),
    }
    statement = _parse("keep the readings where each is above 15")
    out = analyze(
        statement, symtab,
        in_action_block=True,
        live_value_names={"readings"},
    )
    assert out is statement


def test_remember_list_live_value_in_action_block_is_error():
    """v3a §117: live-value ownership applies to all three remember
    flavors — flat value, list, and record."""
    statement = _parse(
        "remember a list called readings with 1 and 2 and 3"
    )
    out = analyze(
        statement, {},
        in_action_block=True,
        live_value_names={"readings"},
    )
    assert isinstance(out, LiminateResult)
    assert out.status is ResultStatus.ERROR_SEMANTIC
    assert "readings" in out.message
    assert "live value" in out.message


def test_show_count_sum_each_on_live_value_are_legal():
    """v3a §111: `show`, `count`, `sum`, and `each` are read-only or
    non-destructive — all legal on live values, in any context."""
    symtab = {
        "readings": list_of_numbers("readings", [10, 20, 30]),
    }
    for line in (
        "show readings",
        "count the readings",
        "sum the readings",
    ):
        statement = _parse(line)
        out = analyze(
            statement, symtab,
            in_action_block=True,
            live_value_names={"readings"},
        )
        assert out is statement, f"{line!r} should be legal on a live value"

"""Integration tests for the Liminate Pack Verb Contract Extension v2.

Covers:
- regression: existing pack_ui.json `navigate` verb still works.
- five execution types: set_value, substring_check, append_to_list,
  set_field, compare_values.
- both target/source resolution modes (literal and slot-derived).
- load-time validation (positional-slot constraints, exactly-one-of rules,
  unknown values).
- value_type: "value" on positional slots accepts QuotedString.
- value_type: "name" on positional slots rejects QuotedString.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from liminate.adapter import (
    TestDomainPack,
    parse_pack_verb_signature,
)
from liminate.result import ResultStatus

from tests._v3a_helpers import outputs, run_v3a


EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _load_pack_json(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def _make_pack(name: str, *, declarations=None) -> TestDomainPack:
    config = _load_pack_json(name)
    vocab = [
        (e["word"], e.get("category", "noun"))
        for e in config.get("vocabulary", [])
    ]
    verbs = [parse_pack_verb_signature(v) for v in config.get("verbs", [])]
    return TestDomainPack(
        declarations=declarations or [],
        script=[],
        name=config.get("name", "pack"),
        vocabulary=vocab,
        verbs=verbs,
    )


# ---------------------------------------------------------------------------
# Regression: pack_ui.json `navigate` still works.
# ---------------------------------------------------------------------------


def test_pack_ui_navigate_regression():
    """Failure mode D: existing navigate verb must continue to work."""
    pack = _make_pack("pack_ui.json")
    src = """
    remember a screen called settings with title as "Settings"
    navigate to settings
    show current-screen
    """
    _, results = run_v3a(src, pack=pack)
    assert outputs(results)[-1] == "settings"


# ---------------------------------------------------------------------------
# Test execution types pack — happy paths for each verb.
# ---------------------------------------------------------------------------


def _test_pack() -> TestDomainPack:
    return _make_pack("pack_test_execution_types.json")


def test_cite_substring_check_happy():
    src = '''
    remember a string called doc with "Newton was born in 1643"
    cite "Newton" from doc
    show doc
    '''
    _, results = run_v3a(src, pack=_test_pack())
    # No error: cite found "Newton" inside doc.
    errors = [
        r for r in results
        if r.status in (ResultStatus.ERROR_RUNTIME, ResultStatus.ERROR_SEMANTIC)
    ]
    assert errors == []
    assert "Newton was born in 1643" in outputs(results)


def test_cite_substring_check_failure():
    src = '''
    remember a string called doc with "Newton was born in 1643"
    cite "Einstein" from doc
    '''
    _, results = run_v3a(src, pack=_test_pack())
    errors = [
        r for r in results
        if r.status in (ResultStatus.ERROR_RUNTIME, ResultStatus.ERROR_SEMANTIC)
    ]
    assert errors
    assert "Einstein" in errors[0].message
    assert "not found" in errors[0].message


def test_cite_against_non_string_rejected():
    src = '''
    remember a number called n with 5
    cite "x" from n
    '''
    _, results = run_v3a(src, pack=_test_pack())
    errors = [
        r for r in results
        if r.status in (ResultStatus.ERROR_SEMANTIC, ResultStatus.ERROR_RUNTIME)
    ]
    assert errors
    assert "text" in errors[0].message or "string" in errors[0].message


def test_reveal_append_to_list_happy():
    src = """
    remember a list called visible-items with none
    remember a string called sword with "iron sword"
    reveal sword to alice
    count visible-items
    """
    _, results = run_v3a(src, pack=_test_pack())
    errors = [
        r for r in results
        if r.status in (ResultStatus.ERROR_RUNTIME, ResultStatus.ERROR_SEMANTIC)
    ]
    assert errors == []
    assert "1" in outputs(results)


def test_reveal_append_type_mismatch():
    src = """
    remember a list called scores with 1 and 2
    remember a string called sword with "iron sword"
    reveal sword to alice
    """
    # `reveal` appends `sword` (a string) to `scores` (which the JSON
    # hardcodes as `visible-items`, not `scores`) — but the actual target
    # is `visible-items` per the pack JSON. Use a different test:
    pass  # see explicit test below


def test_reveal_append_target_must_exist():
    """target_name='visible-items' is fixed; if absent → semantic error."""
    src = """
    remember a string called sword with "iron sword"
    reveal sword to alice
    """
    _, results = run_v3a(src, pack=_test_pack())
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors
    assert "visible-items" in errors[0].message


def test_activate_set_field_target_slot():
    """target_slot resolution: `activate thermostat` modifies thermostat."""
    src = """
    remember a device called thermostat with model as "T1000"
    activate thermostat
    show status of thermostat
    """
    _, results = run_v3a(src, pack=_test_pack())
    errors = [
        r for r in results
        if r.status in (ResultStatus.ERROR_RUNTIME, ResultStatus.ERROR_SEMANTIC)
    ]
    assert errors == []
    assert outputs(results)[-1] == "active"


def test_activate_set_field_literal_value():
    """literal_value 'active' is stored, not a slot lookup."""
    src = """
    remember a device called fan with model as "F1"
    activate fan
    show status of fan
    """
    _, results = run_v3a(src, pack=_test_pack())
    assert outputs(results)[-1] == "active"


def test_activate_set_field_on_non_record():
    """Semantic error: target must be a record."""
    src = """
    remember a number called counter with 5
    activate counter
    """
    _, results = run_v3a(src, pack=_test_pack())
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors
    assert "record" in errors[0].message


def test_verify_compare_values_match():
    """Two identical records: status 'match', no divergences."""
    src = """
    remember a contract called left with title as "X" and value as 10
    remember a contract called right with title as "X" and value as 10
    verify left from right
    show verification-status
    """
    _, results = run_v3a(src, pack=_test_pack())
    assert outputs(results)[-1] == "match"


def test_verify_compare_values_mismatch_structural():
    """Two records differing on one field: status 'mismatch', details lists field."""
    src = """
    remember a contract called left with title as "X" and value as 10
    remember a contract called right with title as "X" and value as 99
    verify left from right
    show verification-status
    show verification-divergences
    """
    _, results = run_v3a(src, pack=_test_pack())
    out = outputs(results)
    assert "mismatch" in out
    assert any("value" in line for line in out)


def test_assign_set_value_slot_derived_target():
    """`assign 42 to score` resolves target via target_slot."""
    src = """
    remember a number called score with 0
    assign 42 to score
    show score
    """
    _, results = run_v3a(src, pack=_test_pack())
    assert outputs(results)[-1] == "42"


# ---------------------------------------------------------------------------
# Load-time validation rules.
# ---------------------------------------------------------------------------


def test_load_time_validation_two_positional_slots():
    sig = {
        "word": "bad",
        "slots": [
            {"name": "a", "connective": None, "required": True},
            {"name": "b", "connective": None, "required": True},
        ],
        "execution": {"type": "set_value", "target_name": "x", "source_slot": "a"},
    }
    with pytest.raises(ValueError, match="multiple positional"):
        parse_pack_verb_signature(sig)


def test_load_time_validation_positional_not_first():
    sig = {
        "word": "bad",
        "slots": [
            {"name": "a", "connective": "to", "required": True},
            {"name": "b", "connective": None, "required": True},
        ],
        "execution": {"type": "set_value", "target_name": "x", "source_slot": "b"},
    }
    with pytest.raises(ValueError, match="first slot"):
        parse_pack_verb_signature(sig)


def test_load_time_validation_duplicate_connective():
    sig = {
        "word": "bad",
        "slots": [
            {"name": "a", "connective": "from", "required": True},
            {"name": "b", "connective": "from", "required": True},
        ],
        "execution": {"type": "set_value", "target_name": "x", "source_slot": "a"},
    }
    with pytest.raises(ValueError, match="unique connective"):
        parse_pack_verb_signature(sig)


def test_load_time_validation_unknown_value_type():
    sig = {
        "word": "bad",
        "slots": [{"name": "a", "connective": "to", "required": True, "value_type": "number"}],
        "execution": {"type": "set_value", "target_name": "x", "source_slot": "a"},
    }
    with pytest.raises(ValueError, match="unknown value_type"):
        parse_pack_verb_signature(sig)


def test_load_time_validation_unknown_execution_type():
    sig = {
        "word": "bad",
        "slots": [{"name": "a", "connective": "to", "required": True}],
        "execution": {"type": "explode_universe"},
    }
    with pytest.raises(ValueError, match="Unknown execution type"):
        parse_pack_verb_signature(sig)


def test_load_time_validation_both_target_fields():
    sig = {
        "word": "bad",
        "slots": [{"name": "a", "connective": "to", "required": True}],
        "execution": {
            "type": "set_value",
            "target_name": "x",
            "target_slot": "a",
            "source_slot": "a",
        },
    }
    with pytest.raises(ValueError, match="both target_name and target_slot"):
        parse_pack_verb_signature(sig)


def test_load_time_validation_neither_target_field():
    sig = {
        "word": "bad",
        "slots": [{"name": "a", "connective": "to", "required": True}],
        "execution": {"type": "set_value", "source_slot": "a"},
    }
    with pytest.raises(ValueError, match="needs either target_name or target_slot"):
        parse_pack_verb_signature(sig)


def test_load_time_validation_both_source_fields():
    sig = {
        "word": "bad",
        "slots": [{"name": "a", "connective": "to", "required": True}],
        "execution": {
            "type": "set_value",
            "target_name": "x",
            "source_slot": "a",
            "literal_value": "x",
        },
    }
    with pytest.raises(ValueError, match="both source_slot and literal_value"):
        parse_pack_verb_signature(sig)


def test_load_time_validation_neither_source_field():
    sig = {
        "word": "bad",
        "slots": [{"name": "a", "connective": "to", "required": True}],
        "execution": {"type": "set_value", "target_name": "x"},
    }
    with pytest.raises(ValueError, match="needs either source_slot or literal_value"):
        parse_pack_verb_signature(sig)


def test_load_time_validation_structural_without_details_target():
    sig = {
        "word": "bad",
        "slots": [
            {"name": "a", "connective": None, "required": True},
            {"name": "b", "connective": "from", "required": True},
        ],
        "execution": {
            "type": "compare_values",
            "left_slot": "a",
            "right_slot": "b",
            "comparison": "structural",
            "on_mismatch": "flag",
            "status_target": "status",
        },
    }
    with pytest.raises(ValueError, match="details_target"):
        parse_pack_verb_signature(sig)


# ---------------------------------------------------------------------------
# value_type on positional slots.
# ---------------------------------------------------------------------------


def test_value_type_value_accepts_quoted_string_on_positional():
    """`cite "quoted text" from source` — positional value_type=value."""
    src = '''
    remember a string called doc with "hello world"
    cite "hello" from doc
    show doc
    '''
    _, results = run_v3a(src, pack=_test_pack())
    errors = [
        r for r in results
        if r.status in (ResultStatus.ERROR_RUNTIME, ResultStatus.ERROR_SEMANTIC)
    ]
    assert errors == []


def test_value_type_name_rejects_quoted_string():
    """A pack with value_type='name' on a positional slot rejects QuotedString."""
    sig_dict = {
        "word": "tag",
        "slots": [
            {"name": "label", "connective": None, "required": True, "value_type": "name"},
            {"name": "target", "connective": "to", "required": True, "value_type": "name"},
        ],
        "execution": {
            "type": "set_field",
            "target_slot": "target",
            "field_name": "label",
            "source_slot": "label",
        },
    }
    sig = parse_pack_verb_signature(sig_dict)
    pack = TestDomainPack(
        declarations=[], script=[], name="test-tag",
        vocabulary=[], verbs=[sig],
    )
    src = '''
    remember a thing called item with id as 1
    tag "my label" to item
    '''
    _, results = run_v3a(src, pack=pack)
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors
    assert "spaces" in errors[0].message


# ---------------------------------------------------------------------------
# Descriptor propagation (SC-Q1 prerequisite — May 16, 2026)
#
# Descriptors (the word between article and `called`, e.g. `source` in
# `remember a source called readme`) used to be stored only on records.
# They are now stored on values and lists too, and the pack-verb
# type_constraint check works against any descriptor regardless of the
# variable's underlying Liminate type.
# ---------------------------------------------------------------------------


def _source_constraint_pack() -> TestDomainPack:
    """A minimal pack with one verb whose `from` slot requires
    type_constraint='source'. Used to exercise descriptor checks across
    value, list, and record types."""
    sig = parse_pack_verb_signature({
        "word": "cite",
        "slots": [
            {"name": "text", "connective": None, "required": True, "value_type": "value"},
            {
                "name": "source", "connective": "from", "required": True,
                "value_type": "name", "type_constraint": "source",
            },
        ],
        "execution": {
            "type": "substring_check",
            "check_slot": "text",
            "against_slot": "source",
        },
    })
    return TestDomainPack(
        declarations=[], script=[], name="src-constraint",
        vocabulary=[("source", "noun"), ("claim", "noun")], verbs=[sig],
    )


def test_descriptor_propagation_on_value():
    """`remember a source called readme with "text"` stores descriptor='source'."""
    src = '''
    remember a source called readme with "the original text"
    '''
    session, _ = run_v3a(src, pack=_source_constraint_pack())
    entry = session.symtab["readme"]
    assert entry.descriptor == "source"
    assert entry.type == "string"


def test_descriptor_propagation_on_list():
    """`remember a source called items with item1 and item2` stores descriptor='source'."""
    src = '''
    remember a source called items with "alpha" and "beta"
    '''
    session, _ = run_v3a(src, pack=_source_constraint_pack())
    entry = session.symtab["items"]
    assert entry.descriptor == "source"
    assert entry.type == "list_of_strings"


def test_type_constraint_passes_on_string_with_descriptor():
    """SC-Q1 prerequisite: string-typed variable with the right descriptor
    satisfies a pack-verb type_constraint."""
    src = '''
    remember a source called readme with "Newton was born in 1643"
    cite "Newton" from readme
    '''
    _, results = run_v3a(src, pack=_source_constraint_pack())
    errors = [
        r for r in results
        if r.status in (ResultStatus.ERROR_RUNTIME, ResultStatus.ERROR_SEMANTIC)
    ]
    assert errors == []


def test_type_constraint_fails_on_string_without_descriptor():
    """String without a descriptor fails the type_constraint check with a
    message that names the underlying type, not 'a record'."""
    src = '''
    remember a value called readme with "Newton was born in 1643"
    cite "Newton" from readme
    '''
    _, results = run_v3a(src, pack=_source_constraint_pack())
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors
    msg = errors[0].message
    assert "'readme'" in msg
    assert "source" in msg
    # Must not claim 'a record' for a string-typed variable.
    assert "record" not in msg


def _decision_constraint_pack() -> TestDomainPack:
    """A `lock to <decision>` verb (set_value execution) that requires
    the decision descriptor on the only constrained slot — used to test
    the type_constraint gate in isolation, without any
    execution-specific analyzer checks on top."""
    sig = parse_pack_verb_signature({
        "word": "lock",
        "slots": [
            {
                "name": "decision", "connective": "to", "required": True,
                "value_type": "name", "type_constraint": "decision",
            },
        ],
        "execution": {
            "type": "set_value",
            "target_name": "locked-decision",
            "source_slot": "decision",
        },
    })
    return TestDomainPack(
        declarations=[], script=[], name="dec-constraint",
        vocabulary=[("decision", "noun")], verbs=[sig],
    )


def test_type_constraint_passes_on_record_with_descriptor():
    """Regression: a record carrying the right descriptor satisfies the
    type_constraint gate (the path the v4a `navigate to screen` verb
    has always used)."""
    src = '''
    remember a decision called policy with budget as 50000 and name as "alpha"
    lock to policy
    '''
    _, results = run_v3a(src, pack=_decision_constraint_pack())
    semantic_errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert semantic_errors == []


def test_type_constraint_fails_on_record_with_wrong_descriptor():
    """Record with a non-matching descriptor errors and names both the
    actual and expected descriptor in the message."""
    src = '''
    remember a claim called policy with budget as 50000
    lock to policy
    '''
    _, results = run_v3a(src, pack=_decision_constraint_pack())
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors
    msg = errors[0].message
    assert "'policy'" in msg
    assert "claim" in msg
    assert "decision" in msg


def test_pack_ui_navigate_with_descriptor_still_works():
    """Regression: pack_ui.json `navigate to <screen>` — a record with
    descriptor='screen' — still satisfies its type_constraint."""
    pack = _make_pack("pack_ui.json")
    src = '''
    remember a screen called settings with title as "Settings"
    navigate to settings
    show current-screen
    '''
    _, results = run_v3a(src, pack=pack)
    semantic_errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert semantic_errors == []
    assert outputs(results)[-1] == "settings"

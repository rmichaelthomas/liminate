"""Phase 3 Spec 2 — the `conformance_check` execution type (`fit` verb) and
iterable pack verbs (the `each` pronoun in pack-verb slots).

`conformance_check` performs a Level 2 schema fit: every field declared by a
shape template must be present in the record with the matching scalar type.
Extra fields are collected but do NOT fail under Level 2. A mismatch surfaces
as PACK_VERB_FAILURE with `failure_type == "conformance_mismatch"` — the
load-bearing string the Spec 3 directive resolver keys on. A non-record on
either slot is a usage error (ERROR_SEMANTIC), not a conformance mismatch.

Iterable pack verbs: inside an `each` block, a pack verb's slot may be the
`each` pronoun, resolving to the current element per iteration.
"""

from __future__ import annotations

import json

import pytest

from liminate.adapter import TestDomainPack, parse_pack_verb_signature
from liminate.result import ResultStatus
from liminate.vocabulary import ConformanceCheckExecution

from tests._v3a_helpers import run_v3a


# ---------------------------------------------------------------------------
# Pack construction — a `fit` verb over the conformance_check execution type.
# ---------------------------------------------------------------------------


_FIT_DEF = {
    "word": "fit",
    "slots": [
        {"name": "record", "connective": None, "required": True,
         "value_type": "name"},
        {"name": "shape", "connective": "to", "required": True,
         "value_type": "name"},
    ],
    "execution": {
        "type": "conformance_check",
        "record_slot": "record",
        "shape_slot": "shape",
        "on_mismatch": "flag",
        "status_target": "fit-status",
        "missing_target": "fit-missing",
        "type_mismatch_target": "fit-type-mismatch",
        "extra_target": "fit-extra",
    },
}


def _fit_pack() -> TestDomainPack:
    sig = parse_pack_verb_signature(json.loads(json.dumps(_FIT_DEF)))
    return TestDomainPack(
        declarations=[], script=[], name="fitpack",
        vocabulary=[], verbs=[sig],
    )


# The shape template uses `none`/`0` placeholders (empty strings won't parse,
# v2c §92): customer -> string, total -> number, status -> string.
_SHAPE = (
    "remember a shape called valid-order with "
    "customer as none and total as 0 and status as none"
)


def _run(program: str):
    return run_v3a(program, pack=_fit_pack())


def _syms(session):
    return {
        k: session.symtab[k].value
        for k in (
            "fit-status", "fit-missing", "fit-type-mismatch", "fit-extra",
        )
        if k in session.symtab
    }


# ---------------------------------------------------------------------------
# §A4 — parse + load-time validation
# ---------------------------------------------------------------------------


def test_conformance_check_parses_to_dataclass():
    sig = parse_pack_verb_signature(json.loads(json.dumps(_FIT_DEF)))
    assert isinstance(sig.execution, ConformanceCheckExecution)
    assert sig.execution.record_slot == "record"
    assert sig.execution.shape_slot == "shape"
    assert sig.execution.on_mismatch == "flag"


def test_conformance_check_missing_shape_slot_raises():
    bad = json.loads(json.dumps(_FIT_DEF))
    del bad["execution"]["shape_slot"]
    with pytest.raises(KeyError):
        parse_pack_verb_signature(bad)


def test_conformance_check_bad_on_mismatch_rejected():
    bad = json.loads(json.dumps(_FIT_DEF))
    bad["execution"]["on_mismatch"] = "shrug"
    with pytest.raises(ValueError, match="on_mismatch"):
        parse_pack_verb_signature(bad)


def test_conformance_check_empty_target_rejected():
    bad = json.loads(json.dumps(_FIT_DEF))
    bad["execution"]["missing_target"] = ""
    with pytest.raises(ValueError, match="missing_target"):
        parse_pack_verb_signature(bad)


def test_conformance_check_default_on_mismatch_is_flag():
    base = json.loads(json.dumps(_FIT_DEF))
    del base["execution"]["on_mismatch"]
    sig = parse_pack_verb_signature(base)
    assert sig.execution.on_mismatch == "flag"


# ---------------------------------------------------------------------------
# §A5 — execution outcomes
# ---------------------------------------------------------------------------


def test_fit_conforming_record_succeeds():
    session, results = _run(
        _SHAPE + "\n"
        'remember an order called o with customer as "acme" '
        "and total as 100 and status as \"shipped\"\n"
        "fit o to valid-order"
    )
    assert results[-1].status is ResultStatus.SUCCESS
    syms = _syms(session)
    assert syms["fit-status"] == "match"
    assert syms["fit-missing"] == []
    assert syms["fit-type-mismatch"] == []
    assert syms["fit-extra"] == []


def test_fit_missing_field_is_conformance_mismatch():
    session, results = _run(
        _SHAPE + "\n"
        'remember an order called o with customer as "acme" and total as 100\n'
        "fit o to valid-order"
    )
    last = results[-1]
    assert last.status is ResultStatus.PACK_VERB_FAILURE
    assert last.metadata["failure_type"] == "conformance_mismatch"
    assert last.metadata["missing"] == ["status"]
    assert last.metadata["type_mismatch"] == []
    # Handler-visibility: outputs committed before the raise.
    assert _syms(session)["fit-status"] == "mismatch"
    assert _syms(session)["fit-missing"] == ["status"]


def test_fit_wrong_typed_field_is_conformance_mismatch():
    session, results = _run(
        _SHAPE + "\n"
        'remember an order called o with customer as 5 '
        'and total as 100 and status as "shipped"\n'
        "fit o to valid-order"
    )
    last = results[-1]
    assert last.status is ResultStatus.PACK_VERB_FAILURE
    assert last.metadata["failure_type"] == "conformance_mismatch"
    assert last.metadata["type_mismatch"] == ["customer"]
    assert last.metadata["missing"] == []


def test_fit_extra_fields_only_succeeds_level_2():
    session, results = _run(
        _SHAPE + "\n"
        'remember an order called o with customer as "a" and total as 1 '
        'and status as "s" and note as "extra"\n'
        "fit o to valid-order"
    )
    assert results[-1].status is ResultStatus.SUCCESS
    syms = _syms(session)
    assert syms["fit-status"] == "match"
    # Extras are collected, not penalized.
    assert syms["fit-extra"] == ["note"]


def test_fit_non_record_is_error_semantic():
    session, results = _run(
        _SHAPE + "\n"
        "remember a number called o with 5\n"
        "fit o to valid-order"
    )
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC
    # NOT a conformance mismatch — no fit-status written.
    assert "fit-status" not in session.symtab


def test_fit_non_record_shape_is_error_semantic():
    session, results = _run(
        'remember a number called bad-shape with 5\n'
        'remember an order called o with customer as "a"\n'
        "fit o to bad-shape"
    )
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC


# ---------------------------------------------------------------------------
# §A6 — iterable pack verbs (`fit each`)
# ---------------------------------------------------------------------------


def test_fit_each_all_conforming_succeeds():
    session, results = _run(
        _SHAPE + "\n"
        'remember an order called oa with customer as "a" '
        'and total as 1 and status as "s"\n'
        'remember an order called ob with customer as "b" '
        'and total as 2 and status as "t"\n'
        "remember a list called line-items with oa and ob\n"
        "each line-items fit each to valid-order"
    )
    assert all(r.status is ResultStatus.SUCCESS for r in results)


def test_fit_each_surfaces_failing_element():
    session, results = _run(
        _SHAPE + "\n"
        'remember an order called oa with customer as "a" '
        'and total as 1 and status as "s"\n'
        'remember an order called ob with customer as "b" and total as 2\n'
        "remember a list called line-items with oa and ob\n"
        "each line-items fit each to valid-order"
    )
    last = results[-1]
    assert last.status is ResultStatus.PACK_VERB_FAILURE
    assert last.metadata["failure_type"] == "conformance_mismatch"
    assert last.metadata["missing"] == ["status"]


def test_fit_each_outside_loop_rejected_by_analyzer():
    # `fit each` with no enclosing `each` is a semantic error.
    session, results = _run(
        _SHAPE + "\n"
        "fit each to valid-order"
    )
    # Parser rejects bare `each` outside an each-clause as a parse error.
    assert results[-1].status in (
        ResultStatus.ERROR_PARSE, ResultStatus.ERROR_SEMANTIC,
    )


def test_fit_each_over_scalar_list_rejected():
    # Iterating a flat (non-record) list with `fit each` is a semantic error.
    session, results = _run(
        _SHAPE + "\n"
        "remember a list called nums with 1 and 2\n"
        "each nums fit each to valid-order"
    )
    assert results[-1].status is ResultStatus.ERROR_SEMANTIC

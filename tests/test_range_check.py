"""Phase 3 D-8 — the `range_check` execution type and the `validate` pack verb.

`range_check` extracts a (low, high) pair from a claimed range string and a
reference window string, compares them exactly, and reports which endpoints
diverge. The research pack exposes it as the `validate` verb operating on
`window`-typed symbols. A non-match (mismatch or parse_error) surfaces as
PACK_VERB_FAILURE, with all four outputs stored before the raise.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from liminate.adapter import TestDomainPack, parse_pack_verb_signature
from liminate.result import ResultStatus
from liminate.vocabulary import RangeCheckExecution

from tests._v3a_helpers import run_v3a


def _load_research_pack() -> TestDomainPack:
    path = (
        Path(__file__).resolve().parent.parent
        / "examples"
        / "pack_research.json"
    )
    config = json.loads(path.read_text(encoding="utf-8"))
    vocab = [
        (e["word"], e.get("category", "noun"))
        for e in config.get("vocabulary", [])
    ]
    verbs = [parse_pack_verb_signature(v) for v in config.get("verbs", [])]
    return TestDomainPack(
        declarations=[],
        script=[],
        name=config.get("name", "research"),
        vocabulary=vocab,
        verbs=verbs,
    )


def _run(claimed: str, window_text: str):
    """Run `validate "<claimed>" from w` against a window holding window_text.
    Returns (session, results)."""
    src = (
        f'remember a window called w with "{window_text}"\n'
        f'validate "{claimed}" from w'
    )
    return run_v3a(src, pack=_load_research_pack())


def _syms(session):
    return {
        k: session.symtab[k].value
        for k in (
            "range-status", "range-claimed",
            "range-reference", "range-divergence",
        )
        if k in session.symtab
    }


# ---------------------------------------------------------------------------
# 1–5, 8–9 — comparison + divergence outcomes
# ---------------------------------------------------------------------------


def test_matching_ranges_with_surrounding_prose():
    """1. `18 to 38` vs `ages 18 to 38` → match, divergence none."""
    session, results = _run("18 to 38", "ages 18 to 38")
    s = _syms(session)
    assert s["range-status"] == "match"
    assert s["range-divergence"] == "none"
    assert s["range-claimed"] == "18 to 38"
    assert s["range-reference"] == "18 to 38"


def test_upper_mismatch():
    """2. `18 to 36` vs `18 to 38` → mismatch, divergence upper."""
    session, _ = _run("18 to 36", "18 to 38")
    s = _syms(session)
    assert s["range-status"] == "mismatch"
    assert s["range-divergence"] == "upper"


def test_lower_mismatch():
    """3. `16 to 38` vs `18 to 38` → mismatch, divergence lower."""
    session, _ = _run("16 to 38", "18 to 38")
    s = _syms(session)
    assert s["range-status"] == "mismatch"
    assert s["range-divergence"] == "lower"


def test_both_mismatch():
    """4. `16 to 36` vs `18 to 38` → mismatch, divergence both."""
    session, _ = _run("16 to 36", "18 to 38")
    s = _syms(session)
    assert s["range-status"] == "mismatch"
    assert s["range-divergence"] == "both"


def test_exact_match_with_prose_on_both_sides():
    """5. `ages 18 to 38` vs `ages 18 to 38` → match."""
    session, _ = _run("ages 18 to 38", "ages 18 to 38")
    s = _syms(session)
    assert s["range-status"] == "match"
    assert s["range-divergence"] == "none"


def test_float_ranges_match():
    """8. `1.5 to 3.5` vs `1.5 to 3.5` → match (float endpoints)."""
    session, _ = _run("1.5 to 3.5", "1.5 to 3.5")
    s = _syms(session)
    assert s["range-status"] == "match"
    assert s["range-claimed"] == "1.5 to 3.5"


def test_negative_numbers_match():
    """9. `-10 to 10` vs `-10 to 10` → match (negative endpoints)."""
    session, _ = _run("-10 to 10", "-10 to 10")
    s = _syms(session)
    assert s["range-status"] == "match"
    assert s["range-claimed"] == "-10 to 10"


# ---------------------------------------------------------------------------
# 6–7 — parse errors
# ---------------------------------------------------------------------------


def test_parse_error_no_numbers():
    """6. Reference with no numbers → parse_error."""
    session, results = _run("18 to 36", "no numbers here")
    s = _syms(session)
    assert s["range-status"] == "parse_error"
    assert any(r.status is ResultStatus.PACK_VERB_FAILURE for r in results)


def test_parse_error_only_one_number():
    """7. Only one number found → parse_error."""
    session, results = _run("18 to 36", "just 18 alone")
    s = _syms(session)
    assert s["range-status"] == "parse_error"
    assert any(r.status is ResultStatus.PACK_VERB_FAILURE for r in results)


# ---------------------------------------------------------------------------
# 10–11 — failure semantics + store-before-raise
# ---------------------------------------------------------------------------


def test_mismatch_raises_pack_verb_failure():
    """10. A mismatch surfaces as PACK_VERB_FAILURE."""
    _, results = _run("18 to 36", "18 to 38")
    failures = [r for r in results if r.status is ResultStatus.PACK_VERB_FAILURE]
    assert failures
    assert "w" in failures[0].message


def test_outputs_stored_before_failure_raises():
    """11. All four symbol outputs are committed before the raise so handlers
    can observe them."""
    session, results = _run("16 to 36", "18 to 38")
    s = _syms(session)
    # Even though the verb raised, every output is present.
    assert s["range-status"] == "mismatch"
    assert s["range-claimed"] == "16 to 36"
    assert s["range-reference"] == "18 to 38"
    assert s["range-divergence"] == "both"


# ---------------------------------------------------------------------------
# 12–14 — pack loading + load-time validation
# ---------------------------------------------------------------------------


def test_validate_verb_loads_from_research_pack():
    """12. The `validate` verb parses and exposes a RangeCheckExecution."""
    pack = _load_research_pack()
    verbs = {v.word: v for v in pack.verbs()}
    assert "validate" in verbs
    assert isinstance(verbs["validate"].execution, RangeCheckExecution)


def test_validate_rejects_non_window_type_constraint():
    """13. The `reference` slot's `window` type_constraint is enforced — a
    non-window symbol is rejected."""
    src = (
        'remember a release called r with "ages 18 to 38"\n'
        'validate "18 to 38" from r'
    )
    _, results = run_v3a(src, pack=_load_research_pack())
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors
    assert "window" in errors[0].message


def test_range_check_load_time_validation_rules_pass():
    """14. A well-formed range_check signature passes load-time validation,
    and bad ones are rejected."""
    base = {
        "word": "validate",
        "slots": [
            {"name": "claimed", "connective": None, "required": True,
             "value_type": "value"},
            {"name": "reference", "connective": "from", "required": True,
             "value_type": "name", "type_constraint": "window"},
        ],
        "execution": {
            "type": "range_check",
            "check_slot": "claimed",
            "against_slot": "reference",
            "on_mismatch": "flag",
            "status_target": "range-status",
            "claimed_target": "range-claimed",
            "reference_target": "range-reference",
            "divergence_target": "range-divergence",
        },
    }
    sig = parse_pack_verb_signature(base)
    assert isinstance(sig.execution, RangeCheckExecution)

    # Bad on_mismatch is rejected.
    bad_mode = json.loads(json.dumps(base))
    bad_mode["execution"]["on_mismatch"] = "shrug"
    with pytest.raises(ValueError, match="on_mismatch"):
        parse_pack_verb_signature(bad_mode)

    # Empty target is rejected.
    bad_target = json.loads(json.dumps(base))
    bad_target["execution"]["divergence_target"] = ""
    with pytest.raises(ValueError, match="divergence_target"):
        parse_pack_verb_signature(bad_target)


# ---------------------------------------------------------------------------
# 15 — integration
# ---------------------------------------------------------------------------


def test_integration_validate_surfaces_mismatch():
    """15. A full program: a valid window, then a mismatching validate whose
    failure surfaces correctly while outputs remain inspectable."""
    src = (
        'remember a window called coverage with "ages 18 to 38, May 2026"\n'
        'validate "18 to 40" from coverage'
    )
    session, results = run_v3a(src, pack=_load_research_pack())
    failures = [r for r in results if r.status is ResultStatus.PACK_VERB_FAILURE]
    assert failures
    s = _syms(session)
    assert s["range-status"] == "mismatch"
    assert s["range-divergence"] == "upper"

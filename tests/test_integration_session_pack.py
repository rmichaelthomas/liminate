"""Integration tests for the session domain pack (cite, verify).

The session pack ships in examples/pack_session.json. This test file
loads the pack from that JSON (keeping test and artifact in lockstep)
and covers happy paths, type-constraint errors, and parse errors for
both verbs.

Pack vocabulary:
  Nouns: claim, source, decision
  Verbs: cite (substring_check), verify (compare_values / structural / flag)

Test structure mirrors test_integration_v4a.py: load pack once, run
targeted programs, assert on result status and symbol-table state.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from liminate.adapter import TestDomainPack, parse_pack_verb_signature
from liminate.result import ResultStatus

from tests._v3a_helpers import outputs, run_v3a


# ---------------------------------------------------------------------------
# Pack loader (mirrors v4a pattern — ties test to JSON artifact)
# ---------------------------------------------------------------------------


def _load_session_pack() -> TestDomainPack:
    """Construct the session pack from examples/pack_session.json."""
    path = (
        Path(__file__).resolve().parent.parent
        / "examples"
        / "pack_session.json"
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
        name=config.get("name", "session"),
        vocabulary=vocab,
        verbs=verbs,
    )


# ---------------------------------------------------------------------------
# cite — happy path
# ---------------------------------------------------------------------------


def test_cite_text_found_in_source():
    """cite succeeds when the quoted text is a substring of the source."""
    _, results = run_v3a(
        """
        remember a source called readme with "Liminate ships with 11 verbs and 35 reserved words."
        cite "11 verbs" from readme
        """,
        pack=_load_session_pack(),
    )
    successes = [r for r in results if r.status is ResultStatus.SUCCESS]
    assert len(successes) == 2, results
    assert successes[1].canonical == 'cite "11 verbs" from readme'


def test_cite_multiple_facts_from_same_source():
    """All three cite calls pass when facts are present."""
    _, results = run_v3a(
        """
        remember a source called notes with "11 verbs. 35 reserved words. liminate.cli:main."
        cite "11 verbs" from notes
        cite "35 reserved words" from notes
        cite "liminate.cli:main" from notes
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert not errors, errors


# ---------------------------------------------------------------------------
# cite — error paths
# ---------------------------------------------------------------------------


def test_cite_text_not_found_is_pack_verb_failure():
    """cite fails with PACK_VERB_FAILURE when text is absent from source.

    v0.12.0: a substring miss is a data-verification failure, not a
    program bug — it surfaces as PACK_VERB_FAILURE (was ERROR_SEMANTIC).
    """
    _, results = run_v3a(
        """
        remember a source called readme with "Liminate has 11 verbs."
        cite "35 reserved words" from readme
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.PACK_VERB_FAILURE]
    assert errors, results
    assert "35 reserved words" in errors[0].message
    assert "readme" in errors[0].message
    # Structured failure identity (v0.12.0).
    assert errors[0].metadata["verb"] == "cite"
    assert errors[0].metadata["failure_type"] == "substring_not_found"
    assert errors[0].metadata["check_value"] == "35 reserved words"
    assert errors[0].metadata["against_name"] == "readme"


def test_cite_from_non_source_typed_symbol_is_semantic_error():
    """cite requires the from-arg to have descriptor 'source'."""
    _, results = run_v3a(
        """
        remember a value called plain-text with "Liminate has 11 verbs."
        cite "11 verbs" from plain-text
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors, results
    assert "plain-text" in errors[0].message


def test_cite_missing_from_connective_is_parse_error():
    """cite without 'from' is a parse error."""
    _, results = run_v3a(
        """
        remember a source called readme with "Liminate has 11 verbs."
        cite "11 verbs" readme
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results
    assert "cite" in errors[0].message


# ---------------------------------------------------------------------------
# verify — happy path: records match
# ---------------------------------------------------------------------------


def test_verify_matching_records_sets_status_match():
    """verify writes 'match' when claim and source records agree."""
    session, results = run_v3a(
        """
        remember a claim called expected with verbs as "11" and reserved-words as "35"
        remember a source called snapshot with verbs as "11" and reserved-words as "35"
        verify expected from snapshot
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert not errors, errors
    assert session.symtab["verification-status"].value == "match"
    assert session.symtab["verification-divergences"].value == []


def test_verify_match_status_is_showable():
    """verification-status can be shown after a match."""
    _, results = run_v3a(
        """
        remember a claim called claim-a with total as "3"
        remember a source called source-a with total as "3"
        verify claim-a from source-a
        show verification-status
        """,
        pack=_load_session_pack(),
    )
    assert outputs(results) == ["match"]


# ---------------------------------------------------------------------------
# verify — diverging records (flag mode — no error)
# ---------------------------------------------------------------------------


def test_verify_diverging_records_flags_mismatch():
    """verify flags mismatches without raising: sets verification-status
    to 'mismatch' and lists divergent field names in verification-divergences."""
    session, results = run_v3a(
        """
        remember a claim called expected with verbs as "11" and reserved-words as "35"
        remember a source called snapshot with verbs as "12" and reserved-words as "35"
        verify expected from snapshot
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert not errors, errors
    assert session.symtab["verification-status"].value == "mismatch"
    assert "verbs" in session.symtab["verification-divergences"].value


def test_verify_mismatch_does_not_halt_execution():
    """Execution continues after a flagged mismatch — on_mismatch is 'flag'."""
    _, results = run_v3a(
        """
        remember a claim called c with x as "1"
        remember a source called s with x as "2"
        verify c from s
        show verification-status
        """,
        pack=_load_session_pack(),
    )
    assert outputs(results) == ["mismatch"]


def test_verify_multiple_divergent_fields():
    """All divergent field names appear in verification-divergences."""
    session, results = run_v3a(
        """
        remember a claim called c with verbs as "11" and adapters as "4" and version as "0.1.0"
        remember a source called s with verbs as "12" and adapters as "3" and version as "0.1.0"
        verify c from s
        """,
        pack=_load_session_pack(),
    )
    divergences = session.symtab["verification-divergences"].value
    assert "verbs" in divergences
    assert "adapters" in divergences
    assert "version" not in divergences


# ---------------------------------------------------------------------------
# verify — type constraint errors
# ---------------------------------------------------------------------------


def test_verify_non_claim_typed_arg_is_semantic_error():
    """The first arg to verify must have descriptor 'claim'."""
    _, results = run_v3a(
        """
        remember a value called not-a-claim with "some text"
        remember a source called s with x as "1"
        verify not-a-claim from s
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors, results
    assert "not-a-claim" in errors[0].message


def test_verify_non_source_typed_arg_is_semantic_error():
    """The from-arg to verify must have descriptor 'source'."""
    _, results = run_v3a(
        """
        remember a claim called c with x as "1"
        remember a value called not-a-source with "text"
        verify c from not-a-source
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors, results
    assert "not-a-source" in errors[0].message


# ---------------------------------------------------------------------------
# Pack noun reservation
# ---------------------------------------------------------------------------


def test_pack_nouns_reserved_when_pack_active():
    """claim, source, and decision are reserved nouns when session pack loads."""
    for reserved_noun in ("claim", "source", "decision"):
        _, results = run_v3a(
            f"remember a value called {reserved_noun} with 5",
            pack=_load_session_pack(),
        )
        errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
        assert errors, f"expected error for reserved noun '{reserved_noun}'"
        assert "reserved in Liminate" in errors[0].message


def test_pack_nouns_usable_as_names_without_pack():
    """claim, source, decision are ordinary names when session pack is absent."""
    for name in ("claim", "source", "decision"):
        session, results = run_v3a(
            f"remember a value called {name} with 5"
        )
        successes = [r for r in results if r.status is ResultStatus.SUCCESS]
        assert successes, f"'{name}' should be usable without the session pack"
        assert session.symtab[name].value == 5


def test_pack_verbs_reserved_when_pack_active():
    """cite and verify are reserved verb tokens when session pack is active."""
    for verb in ("cite", "verify"):
        _, results = run_v3a(
            f"remember a value called {verb} with 5",
            pack=_load_session_pack(),
        )
        errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
        assert errors, f"expected error for reserved verb '{verb}'"
        assert "verb" in errors[0].message


# ---------------------------------------------------------------------------
# measure — happy path: within tolerance
# ---------------------------------------------------------------------------


def test_measure_within_tolerance():
    """measure passes when closest number is within tolerance."""
    session, results = run_v3a(
        """
        remember a source called report with "The cohort held 76 percent of weeks employed."
        measure 76.3 from report within 1
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert not errors, errors
    assert session.symtab["measure-status"].value == "within_tolerance"
    assert session.symtab["measure-matched"].value == 76
    assert session.symtab["measure-delta"].value < 1


def test_measure_exact_match():
    """measure passes with delta 0 when the number matches exactly."""
    session, results = run_v3a(
        """
        remember a source called report with "They held an average of 9.0 jobs."
        measure 9.0 from report within 0.1
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert not errors, errors
    assert session.symtab["measure-status"].value == "within_tolerance"


def test_measure_closest_of_multiple_numbers():
    """measure finds the closest number when source has many."""
    session, results = run_v3a(
        """
        remember a source called report with "78 percent of White workers. 75 percent Hispanic. 68 percent Black."
        measure 78.3 from report within 1
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert not errors, errors
    assert session.symtab["measure-matched"].value == 78
    assert session.symtab["measure-status"].value == "within_tolerance"


# ---------------------------------------------------------------------------
# measure — outside tolerance (flag mode)
# ---------------------------------------------------------------------------


def test_measure_outside_tolerance_flags():
    """measure flags outside_tolerance without halting."""
    session, results = run_v3a(
        """
        remember a source called report with "23 percent of dropouts were limited."
        measure 26.0 from report within 1
        show measure-status
        """,
        pack=_load_session_pack(),
    )
    assert outputs(results) == ["outside_tolerance"]
    assert session.symtab["measure-matched"].value == 23
    assert session.symtab["measure-delta"].value == 3


def test_measure_outside_tolerance_continues_execution():
    """Execution continues after a flagged outside_tolerance."""
    _, results = run_v3a(
        """
        remember a source called report with "The value is 50."
        measure 99 from report within 1
        show measure-status
        show measure-matched
        show measure-delta
        """,
        pack=_load_session_pack(),
    )
    out = outputs(results)
    assert out[0] == "outside_tolerance"
    assert out[1] == "50"
    assert out[2] == "49"


# ---------------------------------------------------------------------------
# measure — no numbers in source
# ---------------------------------------------------------------------------


def test_measure_no_numbers_in_source():
    """measure handles sources with no numeric content."""
    session, results = run_v3a(
        """
        remember a source called report with "No numbers here at all."
        measure 76 from report within 1
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert not errors, errors
    assert session.symtab["measure-status"].value == "no_numbers_found"


# ---------------------------------------------------------------------------
# measure — type constraint errors
# ---------------------------------------------------------------------------


def test_measure_from_non_source_typed_symbol_is_error():
    """measure requires the from-arg to have descriptor 'source'."""
    _, results = run_v3a(
        """
        remember a value called plain-text with "Some text with 42."
        measure 42 from plain-text within 1
        """,
        pack=_load_session_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors, results
    assert "plain-text" in errors[0].message


# ---------------------------------------------------------------------------
# measure — combined with cite
# ---------------------------------------------------------------------------


def test_cite_fails_but_measure_passes():
    """The NLSY97 proof point: cite rejects imprecise text, measure
    confirms numeric proximity."""
    _, results = run_v3a(
        """
        remember a source called bls with "76 percent of weeks employed"
        cite "76.3 percent" from bls
        measure 76.3 from bls within 1
        """,
        pack=_load_session_pack(),
    )
    # v0.12.0: cite's substring miss surfaces as PACK_VERB_FAILURE; the
    # measure passes (within tolerance) so it does not.
    cite_errors = [
        r for r in results if r.status is ResultStatus.PACK_VERB_FAILURE
    ]
    assert len(cite_errors) == 1
    assert "76.3 percent" in cite_errors[0].message


def test_measure_after_cite_in_separate_blocks():
    """When cite and measure are independent checks, both produce results."""
    _, results = run_v3a(
        """
        remember a source called bls with "76 percent of weeks employed"
        measure 76.3 from bls within 1
        show measure-status
        """,
        pack=_load_session_pack(),
    )
    assert outputs(results) == ["within_tolerance"]

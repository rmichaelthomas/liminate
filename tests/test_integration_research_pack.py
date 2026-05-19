"""Integration tests for the research domain pack.

The research pack ships in examples/pack_research.json. It adds release
metadata nouns and a check verb for verifying release identifiers and
coverage windows in AI-summary receipts.
"""

from __future__ import annotations

import json
from pathlib import Path

from liminate.adapter import TestDomainPack, parse_pack_verb_signature
from liminate.result import ResultStatus

from tests._v3a_helpers import outputs, run_v3a
from tests.test_integration_session_pack import _load_session_pack


# ---------------------------------------------------------------------------
# Pack loaders
# ---------------------------------------------------------------------------


def _load_research_pack() -> TestDomainPack:
    """Load the research pack from examples/pack_research.json."""
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


def _load_both_packs() -> tuple[TestDomainPack, TestDomainPack]:
    """Return (session_pack, research_pack) for multi-pack tests."""
    return _load_session_pack(), _load_research_pack()


def _load_merged_pack() -> TestDomainPack:
    """Merge session + research packs for run_v3a's singular pack helper."""
    session_pack, research_pack = _load_both_packs()
    return TestDomainPack(
        declarations=[],
        script=[],
        name="session+research",
        vocabulary=session_pack.vocabulary() + research_pack.vocabulary(),
        verbs=session_pack.verbs() + research_pack.verbs(),
    )


# ---------------------------------------------------------------------------
# check — happy path
# ---------------------------------------------------------------------------


def test_check_identifier_found_in_release():
    """check succeeds when the identifier is a substring of the release."""
    _, results = run_v3a(
        """
        remember a release called bls-release with "USDL-26-0684 | ages 18 to 38 | May 5, 2026"
        check "USDL-26-0684" from bls-release
        """,
        pack=_load_research_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert not errors, errors


def test_check_coverage_found_in_release():
    """check succeeds for coverage window text in the release string."""
    _, results = run_v3a(
        """
        remember a release called bls-release with "USDL-26-0684 | ages 18 to 38 | May 5, 2026"
        check "ages 18 to 38" from bls-release
        """,
        pack=_load_research_pack(),
    )
    successes = [r for r in results if r.status is ResultStatus.SUCCESS]
    assert len(successes) == 2, results
    assert successes[1].canonical == 'check "ages 18 to 38" from bls-release'


def test_check_multiple_fields_in_one_release():
    """Multiple check calls against the same release, all passing."""
    _, results = run_v3a(
        """
        remember a release called bls-release with "USDL-26-0684 | ages 18 to 38 | May 5, 2026"
        check "USDL-26-0684" from bls-release
        check "ages 18 to 38" from bls-release
        check "May 5, 2026" from bls-release
        """,
        pack=_load_research_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert not errors, errors


# ---------------------------------------------------------------------------
# check — error paths
# ---------------------------------------------------------------------------


def test_check_identifier_not_found_is_semantic_error():
    """check fails when the identifier is NOT in the release string."""
    _, results = run_v3a(
        """
        remember a release called bls-release with "USDL-26-0684 | ages 18 to 38"
        check "USDL-24-0626" from bls-release
        """,
        pack=_load_research_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors, results
    assert "USDL-24-0626" in errors[0].message
    assert "bls-release" in errors[0].message


def test_check_wrong_coverage_is_semantic_error():
    """check fails when the coverage window doesn't match."""
    _, results = run_v3a(
        """
        remember a release called bls-release with "USDL-26-0684 | ages 18 to 38"
        check "ages 18 to 36" from bls-release
        """,
        pack=_load_research_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors, results
    assert "ages 18 to 36" in errors[0].message


def test_check_from_non_release_typed_symbol_is_semantic_error():
    """check requires the from-arg to have descriptor 'release'."""
    _, results = run_v3a(
        """
        remember a value called plain with "some text"
        check "some" from plain
        """,
        pack=_load_research_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors, results
    assert "plain" in errors[0].message


def test_check_from_source_typed_symbol_is_semantic_error():
    """check won't accept a source-typed symbol — only release."""
    _, results = run_v3a(
        """
        remember a source called s with "USDL-26-0684"
        check "USDL-26-0684" from s
        """,
        pack=_load_merged_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors, results
    assert "s" in errors[0].message


# ---------------------------------------------------------------------------
# Pack noun reservation
# ---------------------------------------------------------------------------


def test_release_reserved_when_pack_active():
    """'release' is reserved as a noun when the research pack is loaded."""
    _, results = run_v3a(
        "remember a value called release with 5",
        pack=_load_research_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results
    assert "reserved in Liminate" in errors[0].message


def test_window_reserved_when_pack_active():
    """'window' is reserved as a noun when the research pack is loaded."""
    _, results = run_v3a(
        "remember a value called window with 5",
        pack=_load_research_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results
    assert "reserved in Liminate" in errors[0].message


def test_release_usable_as_name_without_pack():
    """'release' is an ordinary name when the research pack is not loaded."""
    session, results = run_v3a("remember a value called release with 5")
    successes = [r for r in results if r.status is ResultStatus.SUCCESS]
    assert successes, results
    assert session.symtab["release"].value == 5


def test_check_reserved_when_pack_active():
    """'check' is reserved as a verb when the research pack is loaded."""
    _, results = run_v3a(
        "remember a value called check with 5",
        pack=_load_research_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results
    assert "verb" in errors[0].message


# ---------------------------------------------------------------------------
# Multi-pack: session + research together
# ---------------------------------------------------------------------------


def test_cite_and_check_together():
    """cite (session pack) and check (research pack) both work in one program."""
    _, results = run_v3a(
        """
        remember a source called bls-prose with "76 percent of weeks employed"
        remember a release called bls-meta with "USDL-26-0684 | ages 18 to 38 | May 5, 2026"
        cite "76 percent" from bls-prose
        check "USDL-26-0684" from bls-meta
        """,
        pack=_load_merged_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert not errors, errors


def test_cite_measure_and_check_together():
    """All three session pack verbs + check work in one program."""
    _, results = run_v3a(
        """
        remember a source called bls with "employed 76 percent of weeks"
        remember a release called meta with "USDL-26-0684 | ages 18 to 38"
        cite "76 percent" from bls
        measure 76.3 from bls within 0.5
        check "USDL-26-0684" from meta
        """,
        pack=_load_merged_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert not errors, errors


def test_check_fails_while_cite_passes():
    """Model cited correct text but wrong release — the NLSY97 experiment case."""
    _, results = run_v3a(
        """
        remember a source called bls with "9.4 jobs from age 18 through age 38"
        remember a release called meta with "USDL-26-0684 | ages 18 to 38"
        cite "9.4 jobs" from bls
        check "USDL-24-0626" from meta
        """,
        pack=_load_merged_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert len(errors) == 1, results
    assert "USDL-24-0626" in errors[0].message
    assert "meta" in errors[0].message


# ---------------------------------------------------------------------------
# window noun — declaration only (no verb operates on it yet)
# ---------------------------------------------------------------------------


def test_window_declaration_stores_value():
    """A window can be declared and its value shown."""
    _, results = run_v3a(
        """
        remember a window called coverage with "18 to 39"
        show coverage
        """,
        pack=_load_research_pack(),
    )
    assert outputs(results) == ["18 to 39"]

"""Tests for pack attribution on LiminateResult metadata.

Receipts Checkpoint v5 §15 dimension 3: when a pack verb resolves a line,
the result carries `metadata["pack"]` naming the pack that contributed the
verb. Base-vocabulary verbs leave the key absent — its absence means
"base vocabulary."

The session pack ships in examples/pack_session.json (name "session",
verbs cite/verify/measure). The tests load it through the same
TestDomainPack path the other pack integration tests use, then drive a
Session so the full parse → execute path runs.
"""
from __future__ import annotations

import json
from pathlib import Path

from liminate.adapter import TestDomainPack, parse_pack_verb_signature
from liminate.cli import Session
from liminate.result import ResultStatus


def _load_session_pack() -> TestDomainPack:
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


def test_pack_verb_carries_pack_name():
    """A pack verb result has metadata['pack'] set to the pack name."""
    pack = _load_session_pack()
    session = Session(domain_packs=[pack])

    session.run_line('remember a source called s with "hello world"')
    result = session.run_line('cite "hello" from s')

    assert result is not None
    assert result.metadata is not None
    assert result.metadata.get("pack") == pack.name()


def test_base_verb_has_no_pack_attribution():
    """A base verb result does NOT carry metadata['pack']."""
    pack = _load_session_pack()
    session = Session(domain_packs=[pack])

    result = session.run_line('remember a string called x with "test"')

    assert result is not None
    if result.metadata is not None:
        assert "pack" not in result.metadata


def test_base_verb_no_pack_loaded():
    """Without any pack, base verbs still carry no pack attribution."""
    session = Session()
    result = session.run_line('remember a string called x with "test"')

    assert result is not None
    if result.metadata is not None:
        assert "pack" not in result.metadata


# ---------------------------------------------------------------------------
# v0.12.0 — structured failure identity on PACK_VERB_FAILURE results
# ---------------------------------------------------------------------------


def test_cite_failure_metadata_structure():
    """A failing cite surfaces PACK_VERB_FAILURE with structured failure
    identity AND pack attribution merged into one metadata dict."""
    pack = _load_session_pack()
    session = Session(domain_packs=[pack])

    session.run_line('remember a source called s with "hello world"')
    result = session.run_line('cite "goodbye" from s')

    assert result is not None
    assert result.status is ResultStatus.PACK_VERB_FAILURE
    md = result.metadata
    assert md is not None
    assert md["verb"] == "cite"
    assert md["failure_type"] == "substring_not_found"
    assert md["check_value"] == "goodbye"
    assert md["against_name"] == "s"
    # Pack attribution is preserved alongside the failure identity.
    assert md["pack"] == pack.name()


def test_verify_mismatch_is_pack_verb_failure_with_metadata():
    """A diverging verify surfaces PACK_VERB_FAILURE with comparison status
    in its failure metadata (was SUCCESS with only a symbol-table flag)."""
    pack = _load_session_pack()
    session = Session(domain_packs=[pack])

    session.run_line(
        'remember a claim called expected with name as "a" and value as 1'
    )
    session.run_line(
        'remember a source called snapshot with name as "a" and value as 2'
    )
    result = session.run_line("verify expected from snapshot")

    assert result is not None
    assert result.status is ResultStatus.PACK_VERB_FAILURE
    md = result.metadata
    assert md is not None
    assert md["verb"] == "verify"
    assert md["failure_type"].startswith("comparison_")
    assert md["status"] != "match"
    assert md["pack"] == pack.name()
    # Symbol-table writes still happen for handler visibility.
    assert session.symtab["verification-status"].value != "match"


def test_measure_outside_tolerance_is_pack_verb_failure_with_metadata():
    """A measure outside tolerance surfaces PACK_VERB_FAILURE carrying the
    claimed/closest/delta/tolerance identity (was SUCCESS with only a flag)."""
    pack = _load_session_pack()
    session = Session(domain_packs=[pack])

    session.run_line('remember a source called bls with "76 percent of weeks"')
    result = session.run_line("measure 90 from bls within 1")

    assert result is not None
    assert result.status is ResultStatus.PACK_VERB_FAILURE
    md = result.metadata
    assert md is not None
    assert md["verb"] == "measure"
    assert md["failure_type"] == "outside_tolerance"
    assert md["claimed"] == 90
    assert md["closest"] == 76
    assert md["delta"] == 14
    assert md["tolerance"] == 1
    assert md["pack"] == pack.name()
    # Symbol-table writes still happen for handler visibility.
    assert session.symtab["measure-status"].value == "outside_tolerance"

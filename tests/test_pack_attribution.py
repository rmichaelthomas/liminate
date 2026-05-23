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

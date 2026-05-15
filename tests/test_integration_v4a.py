"""Phase 1 integration tests for v4a §140 sentences 118–127.

Sentences 118–126 require the UI domain pack (10 nouns + 1 verb,
`navigate`). Sentence 127 tests the back-compat case: pack nouns are
only reserved when the pack is loaded.

The UI pack is built in-process via `TestDomainPack` so the suite does
not depend on file I/O — `examples/pack_ui.json` is the user-facing
artifact; the test pack here mirrors its contents per §134.
"""

from __future__ import annotations

import json
from pathlib import Path

from liminate.adapter import TestDomainPack, parse_pack_verb_signature
from liminate.result import ResultStatus

from tests._v3a_helpers import outputs, run_v3a


def _load_ui_pack() -> TestDomainPack:
    """Construct the UI pack from `examples/pack_ui.json` to keep test
    and example artifact in lockstep — if the JSON drifts from spec
    §134 these tests fail at load time, not silently."""
    path = Path(__file__).resolve().parent.parent / "examples" / "pack_ui.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    vocab = [(e["word"], e.get("category", "noun")) for e in config.get("vocabulary", [])]
    verbs = [parse_pack_verb_signature(v) for v in config.get("verbs", [])]
    return TestDomainPack(
        declarations=[],
        script=[],
        name=config.get("name", "ui"),
        vocabulary=vocab,
        verbs=verbs,
    )


# ---------------------------------------------------------------------------
# Sentence 118 — `navigate to` basic
# ---------------------------------------------------------------------------


def test_sentence_118_navigate_to_basic():
    session, results = run_v3a(
        """
        remember a screen called dashboard with title as "Orders"
        navigate to dashboard
        """,
        pack=_load_ui_pack(),
    )
    successes = [r for r in results if r.status is ResultStatus.SUCCESS]
    assert len(successes) == 2
    assert successes[1].canonical == "navigate to dashboard"
    assert session.symtab["current-screen"].value == "dashboard"


# ---------------------------------------------------------------------------
# Sentence 119 — nonexistent screen (semantic error)
# ---------------------------------------------------------------------------


def test_sentence_119_navigate_to_unknown_name_is_semantic_error():
    _, results = run_v3a(
        """
        navigate to settings
        """,
        pack=_load_ui_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors, results
    assert "settings" in errors[0].message
    assert "remember" in errors[0].message


# ---------------------------------------------------------------------------
# Sentence 120 — non-screen target (semantic error)
# ---------------------------------------------------------------------------


def test_sentence_120_navigate_to_non_screen_is_semantic_error():
    _, results = run_v3a(
        """
        remember a number called counter with 5
        navigate to counter
        """,
        pack=_load_ui_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert errors, results
    # Spec §140 sentence 120 exact wording.
    assert errors[0].message == (
        "'counter' is a number, not a screen. "
        "'navigate to' expects a screen."
    )


# ---------------------------------------------------------------------------
# Sentence 121 — `navigate` without `to` (parse error)
# ---------------------------------------------------------------------------


def test_sentence_121_navigate_without_to_is_parse_error():
    _, results = run_v3a(
        """
        navigate dashboard
        """,
        pack=_load_ui_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results
    assert errors[0].message == (
        "'navigate' needs a destination — try: "
        "navigate to <screen-name>."
    )


# ---------------------------------------------------------------------------
# Sentence 122 — UI component with known fields
# ---------------------------------------------------------------------------


def test_sentence_122_ui_component_known_fields():
    _, results = run_v3a(
        """
        remember a button called submit with label as "Save" and action as save-order
        show label of submit
        """,
        pack=_load_ui_pack(),
    )
    assert outputs(results) == ["Save"]


# ---------------------------------------------------------------------------
# Sentence 123 — UI component with freeform overflow
# ---------------------------------------------------------------------------


def test_sentence_123_ui_component_freeform_field():
    _, results = run_v3a(
        """
        remember a button called submit with label as "Save" and color as blue and size as large
        show color of submit
        """,
        pack=_load_ui_pack(),
    )
    assert outputs(results) == ["blue"]


# ---------------------------------------------------------------------------
# Sentence 124 — `when` handler on UI component
# ---------------------------------------------------------------------------


def test_sentence_124_when_handler_on_ui_component():
    # No adapter pushes are needed — sentence 124 only checks that the
    # handler registers cleanly when the dependency (refresh) exists.
    pack = TestDomainPack(
        declarations=[],
        script=["[done]"],
        name="ui",
        vocabulary=_load_ui_pack().vocabulary(),
        verbs=_load_ui_pack().verbs(),
    )
    session, results = run_v3a(
        """
        remember a button called refresh with label as "Refresh"
        remember a list called orders with order1 and order2
        when refresh is equal to clicked
          show orders
        """,
        pack=pack,
    )
    assert len(session.handler_table.handlers) == 1
    handler = session.handler_table.handlers[0]
    assert "refresh" in handler.dependencies


# ---------------------------------------------------------------------------
# Sentence 125 — `navigate` inside `when` action block
# ---------------------------------------------------------------------------


def test_sentence_125_navigate_inside_when_action_block():
    ui = _load_ui_pack()
    pack = TestDomainPack(
        declarations=[("mode", "string")],
        script=[("mode", "admin"), "[done]"],
        name="ui",
        vocabulary=ui.vocabulary(),
        verbs=ui.verbs(),
    )
    session, results = run_v3a(
        """
        remember a screen called settings with title as "Settings"

        when mode is equal to admin
          navigate to settings
        """,
        pack=pack,
    )
    handler_fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    assert len(handler_fires) == 1
    assert session.symtab["current-screen"].value == "settings"


# ---------------------------------------------------------------------------
# Sentence 126 — pack verb as reserved word in name position
# ---------------------------------------------------------------------------


def test_sentence_126_navigate_reserved_as_verb_when_pack_active():
    _, results = run_v3a(
        """
        remember a value called navigate with 5
        """,
        pack=_load_ui_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results
    assert errors[0].message == (
        "The word 'navigate' is reserved in Liminate — "
        "it's used as a verb. Please choose a different name."
    )


# ---------------------------------------------------------------------------
# Sentence 127 — pack noun as name without pack
# ---------------------------------------------------------------------------


def test_sentence_127_pack_noun_usable_as_name_without_pack():
    session, results = run_v3a(
        """
        remember a value called button with 5
        """,
        # No pack — `button` is not reserved.
    )
    successes = [r for r in results if r.status is ResultStatus.SUCCESS]
    assert len(successes) == 1
    assert session.symtab["button"].value == 5


def test_sentence_127_pack_noun_reserved_when_pack_active():
    # Complement to 127 — with the UI pack active, the same line errors.
    _, results = run_v3a(
        """
        remember a value called button with 5
        """,
        pack=_load_ui_pack(),
    )
    errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert errors, results
    assert "reserved in Liminate" in errors[0].message
    assert "noun" in errors[0].message

"""Phase 11 integration tests for v3a §125 sentences 96–113.

These tests exercise the complete pipeline — source string → Session
(with optional TestDomainPack) → Phase 1 line iteration with `when`
block buffering → Phase 2 listener — and assert on both the displayed
output and the structured InscriptResult stream.

Note on sentence-94/sentence-98-style variable names: a few of the
canonical sentence programs use names that collide with v1 verbs
(`count` in §98, `a`/`b` in §101) or articles (`a`). Those names
can't actually be declared in Inscript because the parser rejects
reserved-word names at definition time. The integration tests use
non-reserved substitutes (`tally` for `count`, `score`/`level` for
`a`/`b`), and the test docstring notes the substitution.
"""

from __future__ import annotations

from inscript.adapter import TestDomainPack
from inscript.result import ResultStatus

from tests._v3a_helpers import run_v3a, fires, outputs


# ---------------------------------------------------------------------------
# Sentence 96 — Basic when handler fires on condition met
# ---------------------------------------------------------------------------


def test_sentence_96_basic_when_fires_on_adapter_update():
    pack = TestDomainPack(
        declarations=[],
        script=[("temperature", 105), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called temperature with 50
        when temperature is above 100
          show "high alert"
        """,
        pack=pack,
    )
    handler_fires = fires(results)
    assert len(handler_fires) == 1
    assert handler_fires[0].output == ["high alert"]
    assert handler_fires[0].metadata["trigger"]["source"] == "adapter_update"


# ---------------------------------------------------------------------------
# Sentence 97 — `when` with `unless` guard suppresses firing
# ---------------------------------------------------------------------------


def test_sentence_97_unless_guard_suppresses_firing():
    pack = TestDomainPack(
        declarations=[],
        script=[("silenced", "true"), ("temperature", 105), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called temperature with 50
        remember a string called silenced with false
        when temperature is above 100 unless silenced is equal to true
          show "alert"
        """,
        pack=pack,
    )
    # Guard is true at the moment temperature crosses 100 → no firing.
    assert fires(results) == []


# ---------------------------------------------------------------------------
# Sentence 98 — `finish` exits listener mode
# ---------------------------------------------------------------------------


def test_sentence_98_finish_exits_listener_mode():
    """Spec sentence 98 uses `count` as a variable name, but `count` is
    a reserved v1 verb (parser rejects it at definition). The test uses
    `tally` instead — semantically identical."""
    pack = TestDomainPack(
        declarations=[],
        script=[("tally", 1), ("tally", 3), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called tally with 0
        when tally is above 2
          finish
        """,
        pack=pack,
    )
    # First update (1) doesn't satisfy; second (3) does → finish.
    shutdowns = [r for r in results if r.status is ResultStatus.SHUTDOWN]
    assert len(shutdowns) == 1
    assert shutdowns[0].metadata["reason"] == "finish"


# ---------------------------------------------------------------------------
# Sentence 99 — Multi-statement action block
# ---------------------------------------------------------------------------


def test_sentence_99_multi_statement_action_block():
    pack = TestDomainPack(
        declarations=[],
        script=[("level", 75), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called level with 0
        when level is above 50
          show "high"
          remember a string called status with active
        """,
        pack=pack,
    )
    handler_fires = fires(results)
    # Two statements in the action block → two HANDLER_FIRE results.
    assert len(handler_fires) == 2
    assert handler_fires[0].output == ["high"]
    # The second statement committed to the symbol table.
    assert session.symtab["status"].value == "active"


# ---------------------------------------------------------------------------
# Sentence 100 — Cascading triggers
# ---------------------------------------------------------------------------


def test_sentence_100_cascading_trigger():
    pack = TestDomainPack(
        declarations=[],
        script=[("temperature", 105), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called temperature with 0
        remember a string called alert with none
        when temperature is above 100
          remember a string called alert with triggered
        when alert is equal to triggered
          show "cascade fired"
        """,
        pack=pack,
    )
    handler_fires = fires(results)
    # Handler 0 fires (no output — just side effect), handler 1 fires
    # via cascade with output.
    cascade_fires = [
        r for r in handler_fires
        if r.metadata["trigger"]["source"] == "cascade"
    ]
    assert len(cascade_fires) == 1
    assert cascade_fires[0].output == ["cascade fired"]


# ---------------------------------------------------------------------------
# Sentence 101 — Cycle detection error
# ---------------------------------------------------------------------------


def test_sentence_101_cycle_detection():
    """Spec sentence 101 uses `a` and `b` as variable names, but `a` is
    an article in Inscript. The test uses `score` and `level`. Also,
    the spec's literal program doesn't actually cycle under §113 deep-
    equality change detection (it sets `a` to the same value it
    already has — silently absorbed). The test exercises the §114
    cycle guard via a true toggling pattern: each handler resets the
    other's trigger, producing a genuine ping-pong."""
    pack = TestDomainPack(
        declarations=[],
        script=[("score", 1), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called score with 0
        remember a number called level with 0
        when score is above 0
          remember a number called score with 0
          remember a number called level with 1
        when level is above 0
          remember a number called level with 0
          remember a number called score with 1
        """,
        pack=pack,
    )
    runtime_errors = [
        r for r in results if r.status is ResultStatus.ERROR_RUNTIME
    ]
    assert any(r.metadata.get("kind") == "cycle" for r in runtime_errors)


# ---------------------------------------------------------------------------
# Sentence 102 — Initial evaluation fires already-true conditions
# ---------------------------------------------------------------------------


def test_sentence_102_initial_evaluation():
    session, results = run_v3a(
        """
        remember a number called level with 75
        when level is above 50
          show "already high"
        """,
        # No pack → no adapters → auto-shutdown after initial eval.
    )
    handler_fires = fires(results)
    assert len(handler_fires) == 1
    assert handler_fires[0].output == ["already high"]
    assert handler_fires[0].metadata["trigger"]["source"] == "initial"
    shutdown = [r for r in results if r.status is ResultStatus.SHUTDOWN][0]
    assert shutdown.metadata["reason"] == "no_adapters"


# ---------------------------------------------------------------------------
# Sentence 103 — `when` with compound condition
# ---------------------------------------------------------------------------


def test_sentence_103_compound_condition():
    pack = TestDomainPack(
        declarations=[],
        script=[
            ("temperature", 105),
            ("humidity", 85),
            "[done]",
        ],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called temperature with 0
        remember a number called humidity with 0
        when temperature is above 100 and humidity is above 80
          show "dangerous"
        """,
        pack=pack,
    )
    handler_fires = fires(results)
    # Only one fire: when humidity crosses 80, both conditions true.
    assert len(handler_fires) == 1
    assert handler_fires[0].output == ["dangerous"]


# ---------------------------------------------------------------------------
# Sentence 104 — `when` with `of` expression (choose-style)
# ---------------------------------------------------------------------------


def test_sentence_104_of_expression_in_condition():
    pack = TestDomainPack(
        declarations=[],
        script=[
            ("patient", {"name": "john", "status": "critical"}),
            "[done]",
        ],
        name="hospital",
    )
    session, results = run_v3a(
        """
        remember a record called patient with name as john and status as stable
        when status of patient is equal to critical
          show "alert"
        """,
        pack=pack,
    )
    handler_fires = fires(results)
    assert len(handler_fires) == 1
    assert handler_fires[0].output == ["alert"]


# ---------------------------------------------------------------------------
# Sentence 105 — Parameterized composition called from action block
# ---------------------------------------------------------------------------


def test_sentence_105_parameterized_composition_in_action():
    pack = TestDomainPack(
        declarations=[],
        script=[("trigger", 1), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a list called readings with 10 and 20 and 30
        remember how to find-high from data: keep the data where each is above 15
        remember a number called trigger with 0
        when trigger is above 0
          remember the result called high-readings from find-high from readings
          show high-readings
        """,
        pack=pack,
    )
    handler_fires = fires(results)
    # Two action statements: capture (silent) + show.
    output_fires = [r for r in handler_fires if r.output]
    assert len(output_fires) == 1
    assert "20, 30" in output_fires[0].output[0]


# ---------------------------------------------------------------------------
# Sentence 106 — `choose` inside `when` action block
# ---------------------------------------------------------------------------


def test_sentence_106_choose_in_action_block():
    pack = TestDomainPack(
        declarations=[],
        script=[("temperature", 105), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called temperature with 0
        remember a string called mode with normal
        when temperature is above 100
          choose if mode is equal to silent: show "logged" otherwise show "alert"
        """,
        pack=pack,
    )
    handler_fires = fires(results)
    # mode is normal → otherwise branch fires → "alert".
    output_fires = [r for r in handler_fires if r.output]
    assert any("alert" in str(r.output) for r in output_fires)


# ---------------------------------------------------------------------------
# Sentence 107 — `finish` inside `choose` branch is immediate and total
# ---------------------------------------------------------------------------


def test_sentence_107a_finish_not_taken_continues():
    """First variant: `critical` is false, so the `otherwise` branch
    (which is `show "warning"`) fires. `show "after choose"` then runs."""
    pack = TestDomainPack(
        declarations=[],
        script=[("temperature", 105), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called temperature with 0
        remember a string called critical with false
        when temperature is above 100
          choose if critical is equal to true: finish otherwise show "warning"
          show "after choose"
        """,
        pack=pack,
    )
    output_lines = outputs(results)
    assert "warning" in output_lines
    assert "after choose" in output_lines
    # No `finish` shutdown — the listener completes via adapter_complete.
    shutdown = [r for r in results if r.status is ResultStatus.SHUTDOWN][0]
    assert shutdown.metadata["reason"] == "adapter_complete"


def test_sentence_107b_finish_taken_immediate_total():
    """Second variant: `critical` is true, so the `if` branch fires
    `finish` — immediate shutdown, no further output."""
    pack = TestDomainPack(
        declarations=[],
        script=[("temperature", 105), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called temperature with 0
        remember a string called critical with true
        when temperature is above 100
          choose if critical is equal to true: finish otherwise show "warning"
          show "after choose"
        """,
        pack=pack,
    )
    output_lines = outputs(results)
    # No output from the action block — finish suppressed everything.
    assert "warning" not in output_lines
    assert "after choose" not in output_lines
    shutdown = [r for r in results if r.status is ResultStatus.SHUTDOWN][0]
    assert shutdown.metadata["reason"] == "finish"


# ---------------------------------------------------------------------------
# Sentence 108 — Unset live value evaluates as condition-false
# ---------------------------------------------------------------------------


def test_sentence_108_unset_live_value_is_false():
    pack = TestDomainPack(
        declarations=[("humidity", "number")],
        script=[("humidity", 85), "[done]"],
        name="weather",
    )
    session, results = run_v3a(
        """
        when humidity is above 80
          show "humid"
        """,
        pack=pack,
    )
    handler_fires = fires(results)
    # No firing during initial evaluation (humidity is unset). One
    # firing after the first update.
    assert len(handler_fires) == 1
    assert handler_fires[0].metadata["trigger"]["source"] == "adapter_update"
    assert handler_fires[0].output == ["humid"]


# ---------------------------------------------------------------------------
# Sentence 109 — Unchanged value produces no re-evaluation
# ---------------------------------------------------------------------------


def test_sentence_109_unchanged_value_no_re_evaluation():
    pack = TestDomainPack(
        declarations=[],
        script=[
            ("level", 50),  # unchanged from Phase 1 — silent absorb
            ("level", 60),  # changed, but condition was already true → no edge
            "[done]",
        ],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called level with 50
        when level is above 40
          show "high"
        """,
        pack=pack,
    )
    handler_fires = fires(results)
    # Only initial-evaluation fire — the adapter updates don't transition
    # the eligibility false→true.
    assert len(handler_fires) == 1
    assert handler_fires[0].metadata["trigger"]["source"] == "initial"


# ---------------------------------------------------------------------------
# Sentence 110 — `remember` cannot overwrite live value
# ---------------------------------------------------------------------------


def test_sentence_110_remember_cannot_overwrite_live_value():
    pack = TestDomainPack(
        declarations=[("temperature", "number")],
        script=[("temperature", 105), "[done]"],
        name="weather",
    )
    session, results = run_v3a(
        """
        when temperature is above 100
          remember a number called temperature with 0
        """,
        pack=pack,
    )
    # When the handler fires, the analyzer rejects the live-value
    # remember at firing time. Either the handler is rejected at
    # registration (in_action_block=True analysis), or the action
    # statement produces ERROR_SEMANTIC during firing. Either way, the
    # word "live value" should appear in the surfaced error.
    error_msgs = " ".join(
        (r.message or "") for r in results
        if r.status in (
            ResultStatus.ERROR_SEMANTIC,
            ResultStatus.ERROR_PARSE,
            ResultStatus.ERROR_RUNTIME,
        )
    )
    assert "live value" in error_msgs.lower() or "temperature" in error_msgs


# ---------------------------------------------------------------------------
# Sentence 111 — No adapters, auto-shutdown after initial evaluation
# ---------------------------------------------------------------------------


def test_sentence_111_no_adapters_auto_shutdown():
    session, results = run_v3a(
        """
        remember a number called score with 10
        when score is above 5
          show "yes"
        """,
    )
    handler_fires = fires(results)
    assert len(handler_fires) == 1
    assert handler_fires[0].output == ["yes"]
    shutdown = [r for r in results if r.status is ResultStatus.SHUTDOWN][0]
    assert shutdown.metadata["reason"] == "no_adapters"
    assert "No event sources" in shutdown.output[0]


# ---------------------------------------------------------------------------
# Sentence 112 — `finish` in composition called from handler
# ---------------------------------------------------------------------------


def test_sentence_112_finish_in_composition_called_from_handler():
    pack = TestDomainPack(
        declarations=[],
        script=[("level", 150), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember how to emergency-stop: finish
        remember a number called level with 0
        when level is above 100
          emergency-stop
          show "after stop"
        """,
        pack=pack,
    )
    output_lines = outputs(results)
    # `finish` inside the composition called from the handler is
    # immediate and total — `show "after stop"` never executes.
    assert "after stop" not in output_lines
    shutdown = [r for r in results if r.status is ResultStatus.SHUTDOWN][0]
    assert shutdown.metadata["reason"] == "finish"


# ---------------------------------------------------------------------------
# Sentence 113 — Phase 1 error prevents Phase 2
# ---------------------------------------------------------------------------


def test_sentence_113_phase1_error_blocks_phase2():
    pack = TestDomainPack(
        declarations=[("temperature", "number")],
        script=[("temperature", 105), "[done]"],
        name="weather",
    )
    session, results = run_v3a(
        """
        when temperature is above 100
          show "hot"
        show missingname
        """,
        pack=pack,
    )
    # Phase 1 ERROR_SEMANTIC fired for `show missingname`.
    semantic_errors = [
        r for r in results if r.status is ResultStatus.ERROR_SEMANTIC
    ]
    assert any("missingname" in (r.message or "") for r in semantic_errors)
    # Phase 2 did not start — no LISTENING marker, no HANDLER_FIRE.
    assert all(r.status is not ResultStatus.LISTENING for r in results)
    assert fires(results) == []


# ---------------------------------------------------------------------------
# Aux: indentation rules (v3a §110)
# ---------------------------------------------------------------------------


def test_when_block_empty_action_is_parse_error():
    """v3a §110: a `when` line with no indented continuation is a parse
    error."""
    pack = TestDomainPack(declarations=[], script=["[done]"], name="t")
    session, results = run_v3a(
        """
        remember a number called level with 0
        when level is above 50
        show "outside the block"
        """,
        pack=pack,
    )
    parse_errors = [
        r for r in results if r.status is ResultStatus.ERROR_PARSE
    ]
    assert any(
        "action block" in (r.message or "").lower() for r in parse_errors
    )


def test_when_block_inconsistent_depth_is_parse_error():
    """v3a §110: indentation deeper than the block's established depth
    is a parse error."""
    pack = TestDomainPack(declarations=[], script=["[done]"], name="t")
    session, results = run_v3a(
        "remember a number called level with 0\n"
        "when level is above 50\n"
        "  show \"first\"\n"
        "    show \"deeper\"\n",
        pack=pack,
    )
    parse_errors = [
        r for r in results if r.status is ResultStatus.ERROR_PARSE
    ]
    assert any("indented" in (r.message or "").lower() for r in parse_errors)


def test_when_block_tab_in_indent_is_parse_error():
    """v3a §110: tabs in the leading whitespace of an action line are
    rejected at the lexer level."""
    pack = TestDomainPack(declarations=[], script=["[done]"], name="t")
    session, results = run_v3a(
        "remember a number called level with 0\n"
        "when level is above 50\n"
        "\tshow \"tab\"\n",
        pack=pack,
    )
    parse_errors = [
        r for r in results if r.status is ResultStatus.ERROR_PARSE
    ]
    assert any("tab" in (r.message or "").lower() for r in parse_errors)

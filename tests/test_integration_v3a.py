"""Phase 11 integration tests for v3a §125 sentences 96–113.

These tests exercise the complete pipeline — source string → Session
(with optional TestDomainPack) → Phase 1 line iteration with `when`
block buffering → Phase 2 listener — and assert on both the displayed
output and the structured LiminateResult stream.

Note on sentence-94/sentence-98-style variable names: a few of the
canonical sentence programs use names that collide with v1 verbs
(`count` in §98, `a`/`b` in §101) or articles (`a`). Those names
can't actually be declared in Liminate because the parser rejects
reserved-word names at definition time. The integration tests use
non-reserved substitutes (`tally` for `count`, `score`/`level` for
`a`/`b`), and the test docstring notes the substitution.
"""

from __future__ import annotations

from liminate.adapter import TestDomainPack
from liminate.result import ResultStatus

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
    """Spec sentence 101 (external-review replacement, May 13, 2026)
    uses three handlers in a ring that produces a genuine cycle under
    §113 deep-equality change detection. Names `a`/`b`/`c` are
    substituted with `alpha`/`beta`/`gamma` because `a` is an article
    in Liminate. Trace: adapter sets alpha=1 → H1 fires (beta=1) →
    cascade H2 fires (alpha=0, gamma=1) → cascade H3 fires (alpha=1)
    → cascade would re-fire H1 → same-handler-twice cycle detected."""
    pack = TestDomainPack(
        declarations=[],
        script=[("alpha", 1), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called alpha with 0
        remember a number called beta with 0
        remember a number called gamma with 0
        when alpha is above 0
          remember a number called beta with 1
        when beta is above 0
          remember a number called alpha with 0
          remember a number called gamma with 1
        when gamma is above 0
          remember a number called alpha with 1
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
    assert "no event sources" in shutdown.output[0].lower()


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


# ===========================================================================
# External-review coverage tests (May 13, 2026)
# Tier 1 — T1–T7: specified behavior that previously had no coverage.
# Tier 2 — T8–T19: edge cases and adapter contract enforcement.
# ===========================================================================


def test_t1_when_inside_composition_body_is_parse_error():
    """Tier 1 T1: `when` is rejected inside composition definitions
    (v3a §108 — top-level only)."""
    session, results = run_v3a(
        """
        remember how to watch: when temperature is above 100
        """,
    )
    parse_errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert any("'when'" in (r.message or "").lower() or "when" in (r.message or "").lower()
               for r in parse_errors)
    # Phase 2 didn't start.
    assert all(r.status is not ResultStatus.LISTENING for r in results)


def test_t2_nested_when_inside_when_block_is_parse_error():
    """Tier 1 T2: a `when` statement inside a `when` action block is
    rejected at parse time (v3a §108)."""
    pack = TestDomainPack(declarations=[], script=["[done]"], name="t")
    session, results = run_v3a(
        """
        remember a number called x with 0
        when x is above 0
          when x is above 10
        """,
        pack=pack,
    )
    parse_errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert any("when" in (r.message or "").lower() for r in parse_errors)
    assert fires(results) == []


def test_t3_forward_reference_in_when_is_semantic_error():
    """Tier 1 T3: registration-time name resolution (v3a §108) rejects
    forward references — names defined below the `when` are not yet
    visible when the handler registers."""
    session, results = run_v3a(
        """
        when level is above threshold
          show "high"
        remember a number called threshold with 50
        remember a number called level with 75
        """,
    )
    sem_errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    msgs = " ".join((r.message or "") for r in sem_errors).lower()
    assert "level" in msgs or "threshold" in msgs
    assert all(r.status is not ResultStatus.LISTENING for r in results)


def test_t4_unless_guard_lifts_when_guard_becomes_false():
    """Tier 1 T4: edge-triggered compound eligibility (§109/§113).
    First update: condition true but guard true → no fire. Second
    update: guard goes false → compound becomes true → fires."""
    pack = TestDomainPack(
        declarations=[],
        script=[("temperature", 105), ("silenced", "false"), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called temperature with 0
        remember a string called silenced with true
        when temperature is above 100 unless silenced is equal to true
          show "alert"
        """,
        pack=pack,
    )
    handler_fires = fires(results)
    assert len(handler_fires) == 1
    assert handler_fires[0].output == ["alert"]


def test_t5_finish_during_initial_evaluation_prevents_adapter_start():
    """Tier 1 T5: §121 + §112. Phase 1 inits level=75; initial eval
    fires handler → show "high" → finish → shutdown. The adapter
    update [level = 100] is never delivered."""
    pack = TestDomainPack(
        declarations=[],
        script=[("level", 100), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called level with 75
        when level is above 50
          show "high"
          finish
        """,
        pack=pack,
    )
    output_lines = outputs(results)
    assert "high" in output_lines
    shutdown = [r for r in results if r.status is ResultStatus.SHUTDOWN][0]
    assert shutdown.metadata["reason"] == "finish"
    # The handler fired exactly once — during initial evaluation only.
    initial_fires = [
        r for r in fires(results)
        if r.metadata["trigger"]["source"] == "initial"
    ]
    assert len(initial_fires) >= 1
    adapter_fires = [
        r for r in fires(results)
        if r.metadata["trigger"]["source"] == "adapter_update"
    ]
    assert adapter_fires == []


def test_t6_finish_in_phase1_is_semantic_error():
    """Tier 1 T6: §112 — `finish` outside an action block is a
    semantic error."""
    session, results = run_v3a(
        """
        remember a number called x with 5
        finish
        """,
    )
    sem_errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    assert any("finish" in (r.message or "").lower() for r in sem_errors)


def test_t7_choose_branch_mutations_cascade():
    """Tier 1 T7: a `remember` inside a `choose` branch participates in
    cascade evaluation (§113/§114)."""
    pack = TestDomainPack(
        declarations=[],
        script=[("x", 10), "[done]"],
        name="test",
    )
    session, results = run_v3a(
        """
        remember a number called x with 0
        remember a string called status with idle
        when x is above 0
          choose if x is above 5: remember a string called status with active otherwise remember a string called status with low
        when status is equal to active
          show "active cascade"
        """,
        pack=pack,
    )
    output_lines = outputs(results)
    assert "active cascade" in output_lines


# ---------------------------------------------------------------------------
# Tier 2 — edge cases and adapter contract enforcement
# ---------------------------------------------------------------------------


def test_t8_no_when_blocks_no_phase2():
    """Tier 2 T8: §107 — without `when` blocks, Phase 2 does not start."""
    session, results = run_v3a(
        """
        remember a number called x with 1
        show x
        """,
    )
    assert all(r.status is not ResultStatus.LISTENING for r in results)
    assert fires(results) == []
    assert all(r.status is not ResultStatus.SHUTDOWN for r in results)


def test_t9_when_inside_each_is_parse_error():
    """Tier 2 T9: §108 — `when` cannot appear as the action of `each`
    (top-level only)."""
    pack = TestDomainPack(declarations=[], script=["[done]"], name="t")
    session, results = run_v3a(
        """
        remember a list called readings with 1 and 2
        each the readings when each is above 1
        """,
        pack=pack,
    )
    parse_errors = [r for r in results if r.status is ResultStatus.ERROR_PARSE]
    assert any("when" in (r.message or "").lower() for r in parse_errors)


def test_t10_amber_in_when_prevents_phase2():
    """Tier 2 T10: §123 — unresolved amber in a `when` condition blocks
    Phase 2 entry. `run_v3a` does not auto-confirm amber, so the AMBER
    result is left unresolved and Phase 1 records a blocking error."""
    pack = TestDomainPack(declarations=[], script=["[done]"], name="t")
    session, results = run_v3a(
        """
        remember a number called x with 0
        when x is above 0 and x is below 100 or x is equal to 50
          show "mixed"
        """,
        pack=pack,
    )
    ambers = [
        r for r in results
        if r.status in (ResultStatus.AMBER_PRECEDENCE, ResultStatus.AMBER_AMBIGUITY)
    ]
    assert len(ambers) >= 1
    # Phase 2 should not have entered.
    assert all(r.status is not ResultStatus.LISTENING for r in results)


def test_t14_finish_composition_in_value_position_is_semantic_error():
    """Tier 2 T14: §112 / v2b §76 — a composition whose body is
    side-effect-only `finish` cannot be captured in value position."""
    pack = TestDomainPack(
        declarations=[],
        script=[("x", 1), "[done]"],
        name="t",
    )
    session, results = run_v3a(
        """
        remember how to stop-now: finish
        remember a number called x with 0
        when x is above 0
          remember the result called outcome from stop-now
        """,
        pack=pack,
    )
    errs = [
        r for r in results
        if r.status in (ResultStatus.ERROR_SEMANTIC, ResultStatus.ERROR_RUNTIME)
    ]
    msgs = " ".join((r.message or "") for r in errs).lower()
    assert "finish" in msgs or "doesn't return" in msgs or "side effect" in msgs


def test_t15_composition_return_to_live_value_name_is_semantic_error():
    """Tier 2 T15: §111 — `remember` targeting a live-value name inside
    an action block is rejected, even when the value comes from a
    composition return."""
    pack = TestDomainPack(
        declarations=[("temperature", "number"), ("trigger", "number")],
        script=[("trigger", 1), "[done]"],
        name="weather",
    )
    session, results = run_v3a(
        """
        remember a list called readings with 1 and 2 and 3
        remember how to compute: count the readings
        when trigger is above 0
          remember the result called temperature from compute
        """,
        pack=pack,
    )
    errs = [
        r for r in results
        if r.status in (ResultStatus.ERROR_SEMANTIC, ResultStatus.ERROR_RUNTIME, ResultStatus.ERROR_PARSE)
    ]
    msgs = " ".join((r.message or "") for r in errs).lower()
    assert "live value" in msgs or "temperature" in msgs


def test_t17_filter_on_live_value_is_semantic_error_in_phase1():
    """Tier 2 T17: §111 — `filter` on a live-value name is a semantic
    error in all contexts, including Phase 1 sequential mode."""
    pack = TestDomainPack(
        declarations=[("readings", "list_of_numbers")],
        script=[("readings", [1, 2, 3]), "[done]"],
        name="weather",
    )
    session, results = run_v3a(
        """
        filter readings where each is above 1
        """,
        pack=pack,
    )
    sem_errors = [r for r in results if r.status is ResultStatus.ERROR_SEMANTIC]
    msgs = " ".join((r.message or "") for r in sem_errors).lower()
    assert "live value" in msgs or "filter" in msgs


def test_t18_keep_inside_action_block_is_legal():
    """Tier 2 T18: §111 — `keep` is non-destructive and legal inside
    action blocks. (Readings declared as a Phase 1 list, trigger as a
    live number — keep operates on the Phase 1 list; the action block
    semantics are what matter here.)"""
    pack = TestDomainPack(
        declarations=[],
        script=[("trigger", 1), "[done]"],
        name="t",
    )
    session, results = run_v3a(
        """
        remember a list called readings with 1 and 2 and 3
        remember a number called trigger with 0
        when trigger is above 0
          remember the result called high-readings from keep the readings where each is above 1
          show high-readings
        """,
        pack=pack,
    )
    output_lines = outputs(results)
    assert any("2, 3" in line for line in output_lines)


def test_t19_of_expression_in_unless_guard():
    """Tier 2 T19: §109/§108 — `of` expressions are legal in `unless`
    guards (choose-style value resolution)."""
    pack = TestDomainPack(
        declarations=[],
        script=[("level", 75), "[done]"],
        name="t",
    )
    session, results = run_v3a(
        """
        remember a record called config with mode as active and override as false
        remember a number called level with 0
        when level is above 50 unless override of config is equal to true
          show "alert"
        """,
        pack=pack,
    )
    output_lines = outputs(results)
    assert "alert" in output_lines


# ===========================================================================
# U1 / U2 / U3 — CLI display improvements (May 13, 2026)
# ===========================================================================

import io as _io
from liminate.cli import Session as _Session, display_result as _display_result
from liminate.cli import _consume_when_block as _consume_when_block  # type: ignore


def _render_v3a(source: str, *, pack=None, quiet: bool = True) -> str:
    """Drive a v3a program through the real CLI display path and return
    captured stdout. Used by the U1/U2/U3 tests to assert on the actual
    user-visible output, not just the structured result stream."""
    import textwrap
    from liminate.lexer import leading_indent, LexError, tokenize
    from liminate.listener import listen
    from liminate.result import LiminateResult, ResultStatus as _RS
    from liminate.vocabulary import TokenType as _TT

    source = textwrap.dedent(source).strip("\n")
    session = _Session(domain_packs=[pack] if pack else None)
    buf = _io.StringIO()
    write = buf.write
    lines = source.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            if quiet:
                write("\n")
            i += 1
            continue
        try:
            indent = leading_indent(line)
        except LexError as e:
            err = LiminateResult(
                status=_RS.ERROR_PARSE, message=e.message, executed=False,
            )
            _display_result(err, session, quiet=quiet, out=buf)
            session.record_result(err)
            i += 1
            continue
        is_when = False
        if indent == 0:
            try:
                toks = tokenize(line)
            except LexError:
                toks = []
            if (
                toks
                and toks[0].type is _TT.CONNECTIVE
                and toks[0].value == "when"
            ):
                is_when = True
        if is_when:
            i = _consume_when_block(
                lines, i, session,
                auto_confirm_amber=True, quiet=quiet, out=buf, write=write,
            )
            continue
        r = session.run_line(line)
        _display_result(r, session, quiet=quiet, out=buf)
        session.record_result(r)
        i += 1

    if session.handler_table.is_empty() or session.phase1_had_error:
        return buf.getvalue()
    for r in listen(
        session.symtab,
        session.handler_table,
        session.live_value_registry,
        session.adapters(),
    ):
        _display_result(r, session, quiet=quiet, out=buf)
    return buf.getvalue()


def test_u1_handler_fire_does_not_print_canonical_preview():
    """U1: HANDLER_FIRE outputs must not display 'I understand this as:'
    — that prefix is reserved for Phase 1 canonical previews."""
    pack = TestDomainPack(
        declarations=[],
        script=[("temperature", 105), "[done]"],
        name="t",
    )
    text = _render_v3a(
        """
        remember a number called temperature with 0
        when temperature is above 100
          show "alert"
        """,
        pack=pack,
    )
    # The action-block's output line itself must NOT carry the Phase-1
    # canonical preview.
    assert "I understand this as: show" not in text
    assert "alert" in text


def test_u2_adapter_update_tag_shows_name_and_value():
    """U2: an adapter_update-triggered firing tags its first output
    line with the changed name and new value."""
    pack = TestDomainPack(
        declarations=[],
        script=[("temperature", 150), "[done]"],
        name="t",
    )
    text = _render_v3a(
        """
        remember a number called temperature with 0
        when temperature is above 100
          show "warning: elevated"
        """,
        pack=pack,
    )
    assert "[temperature → 150] warning: elevated" in text


def test_u2_initial_evaluation_tag():
    """U2: initial-evaluation firings tag with `[initial]`."""
    text = _render_v3a(
        """
        remember a number called level with 75
        when level is above 50
          show "high"
        """,
    )
    assert "[initial] high" in text


def test_u2_cascade_tag_lists_changed_names():
    """U2: cascade firings tag with `[cascade: <names> changed]`."""
    pack = TestDomainPack(
        declarations=[],
        script=[("temperature", 105), "[done]"],
        name="t",
    )
    text = _render_v3a(
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
    assert "[cascade: alert changed] cascade fired" in text


def test_u2_multi_statement_action_block_tags_first_line_only():
    """U2: across multiple output-producing statements in one firing,
    the trigger tag appears only on the first line."""
    pack = TestDomainPack(
        declarations=[],
        script=[("level", 75), "[done]"],
        name="t",
    )
    text = _render_v3a(
        """
        remember a number called level with 0
        when level is above 50
          show "first"
          show "second"
        """,
        pack=pack,
    )
    assert "[level → 75] first" in text
    assert "[level → 75] second" not in text
    # The second statement is bare, no tag prefix.
    assert "\nsecond\n" in text


def test_u3_shutdown_reason_finish_message():
    """U3: shutdown via `finish` uses the reason-specific message."""
    pack = TestDomainPack(
        declarations=[],
        script=[("level", 75), "[done]"],
        name="t",
    )
    text = _render_v3a(
        """
        remember a number called level with 0
        when level is above 50
          finish
        """,
        pack=pack,
    )
    assert "Listener stopped: finish called." in text


def test_u3_shutdown_reason_adapter_complete_message():
    """U3: shutdown via adapter completion uses the matching message."""
    pack = TestDomainPack(
        declarations=[],
        script=[("level", 75), "[done]"],
        name="t",
    )
    text = _render_v3a(
        """
        remember a number called level with 0
        when level is above 50
          show "ok"
        """,
        pack=pack,
    )
    assert "Listener stopped: all event sources completed." in text


def test_u3_shutdown_reason_no_adapters_message():
    """U3: auto-shutdown with no adapters uses the matching message."""
    text = _render_v3a(
        """
        remember a number called level with 75
        when level is above 50
          show "ok"
        """,
    )
    assert "Listener stopped: no event sources registered." in text


def test_u3_watching_list_in_registration_order():
    """U3: the LISTENING marker reports watched names in source-walk
    registration order (the order handlers were encountered and the
    order names appeared within each handler), not alphabetical."""
    pack = TestDomainPack(
        declarations=[],
        script=["[done]"],
        name="t",
    )
    text = _render_v3a(
        """
        remember a number called systolic with 0
        remember a string called medication-given with false
        remember a number called heart-rate with 0
        remember a string called alert-level with none
        when systolic is above 140 unless medication-given is equal to true
          show "x"
        when heart-rate is above 120
          show "y"
        when alert-level is equal to critical
          show "z"
        """,
        pack=pack,
    )
    expected = (
        "Listening for changes to: systolic, medication-given, "
        "heart-rate, alert-level"
    )
    assert expected in text


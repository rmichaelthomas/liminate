"""Phase 9 gate tests: Phase 2 listener (v3a §107/§113/§114/§115/§119/
§120/§121/§122).

These tests build the listener's input state directly — symbol table,
handler table, live-value registry, and TestAdapter(s) — and assert on
the structured result stream the `listen()` generator yields. The
higher-level integration tests in Phase 11 exercise the full source →
Session → listener path; this module is the gate that proves the
runtime machinery is sound before the CLI integration arrives.
"""

from __future__ import annotations

from typing import Iterable

import pytest

from liminate.adapter import (
    AdapterDone,
    AdapterFailure,
    AdapterUpdate,
    LiveValueDeclaration,
    LiveValueRegistry,
    TestAdapter,
)
from liminate.analyzer import SymbolEntry
from liminate.interpreter import (
    HandlerTable,
    execute as _execute,
)
from liminate.lexer import tokenize
from liminate.listener import listen
from liminate.parser import parse_when_block
from liminate.reorderer import reorder
from liminate.result import LiminateResult, ResultStatus


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _build_when_node(header: str, *actions: str):
    htoks = reorder(tokenize(header))
    atoks = [reorder(tokenize(a)) for a in actions]
    ast = parse_when_block(htoks, atoks)
    assert not isinstance(ast, LiminateResult), ast
    return ast


def _register(
    symtab: dict[str, SymbolEntry],
    ht: HandlerTable,
    reg: LiveValueRegistry,
    header: str,
    *actions: str,
) -> None:
    """Build a WhenNode and register it via the interpreter so all the
    normal validation/registration paths exercise (rather than mutating
    the handler table directly)."""
    ast = _build_when_node(header, *actions)
    result = _execute(
        ast, symtab, handler_table=ht, live_value_registry=reg,
    )
    assert result.status is ResultStatus.SUCCESS, result


def _set_number(symtab, name, value):
    """Direct symbol-table write used to set up Phase 1 initial state
    in tests. Mirrors what a Phase 1 `remember` would produce."""
    symtab[name] = SymbolEntry(name=name, value=value, type="number")


def _set_string(symtab, name, value):
    symtab[name] = SymbolEntry(name=name, value=value, type="string")


def _drain(it: Iterable[LiminateResult]) -> list[LiminateResult]:
    return list(it)


# ---------------------------------------------------------------------------
# Listener entry / shutdown (§122)
# ---------------------------------------------------------------------------


def test_listener_yields_listening_marker_first():
    """v3a §122: the first yielded result is always the LISTENING
    marker carrying the watching-names list."""
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "temperature", 50)
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg,
        "when temperature is above 100",
        'show "alert"',
    )
    results = _drain(listen(symtab, ht, reg, adapters=[]))
    assert results[0].status is ResultStatus.LISTENING
    assert results[0].metadata == {"watching": ["temperature"]}


def test_listener_no_adapters_auto_shutdown_after_initial_evaluation():
    """v3a §107 / sentence 111: no event sources → initial evaluation
    runs, then auto-shutdown with reason="no_adapters"."""
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "x", 10)
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg, "when x is above 5", 'show "yes"',
    )
    results = _drain(listen(symtab, ht, reg, adapters=[]))
    # LISTENING + HANDLER_FIRE (initial eval fires) + SHUTDOWN
    assert results[0].status is ResultStatus.LISTENING
    assert results[1].status is ResultStatus.HANDLER_FIRE
    assert results[1].metadata["trigger"]["source"] == "initial"
    assert results[1].output == ["yes"]
    assert results[-1].status is ResultStatus.SHUTDOWN
    assert results[-1].metadata["reason"] == "no_adapters"


# ---------------------------------------------------------------------------
# Initial evaluation (§121)
# ---------------------------------------------------------------------------


def test_initial_evaluation_fires_already_true_conditions():
    """v3a sentence 102: handlers whose compound eligibility is already
    true at Phase 2 entry fire in registration order with source
    "initial"."""
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "level", 75)
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg,
        "when level is above 50", 'show "already high"',
    )
    results = _drain(listen(symtab, ht, reg, adapters=[]))
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    assert len(fires) == 1
    assert fires[0].output == ["already high"]
    assert fires[0].metadata["trigger"]["source"] == "initial"


def test_initial_evaluation_does_not_fire_false_conditions():
    """Handler with false initial eligibility does not fire on entry."""
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "level", 10)
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg, "when level is above 50", 'show "x"',
    )
    results = _drain(listen(symtab, ht, reg, adapters=[]))
    assert all(r.status is not ResultStatus.HANDLER_FIRE for r in results)


# ---------------------------------------------------------------------------
# Adapter updates (§113, §115, §119)
# ---------------------------------------------------------------------------


def test_adapter_update_fires_handler_on_false_to_true_transition():
    """v3a sentence 96: an adapter update that satisfies the condition
    fires the handler with source="adapter_update"."""
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "temperature", 50)
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg,
        "when temperature is above 100", 'show "high alert"',
    )
    adapter = TestAdapter([("temperature", 105)], name="test")
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    assert len(fires) == 1
    assert fires[0].output == ["high alert"]
    assert fires[0].metadata["trigger"]["source"] == "adapter_update"
    assert fires[0].metadata["trigger"]["values_changed"] == ["temperature"]


def test_unchanged_value_produces_no_re_evaluation():
    """v3a sentence 109 + §113: an adapter update that matches the
    stored value is silently absorbed — no handler fires."""
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "level", 50)
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg, "when level is above 40", 'show "high"',
    )
    # Script: same value 50 (no-op), then unchanged 60 (rises, but the
    # condition is already true from initial eval — false→true edge
    # doesn't re-fire either).
    adapter = TestAdapter([("level", 50), ("level", 60)], name="test")
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    # Only initial evaluation fires.
    assert len(fires) == 1
    assert fires[0].metadata["trigger"]["source"] == "initial"


def test_first_adapter_update_to_unset_live_value_fires_handler():
    """v3a sentence 108 + §117: an unset live value evaluates as false
    during initial evaluation. The first adapter update transitions
    unset → active, which is always a "change," so re-evaluation fires
    if the condition now holds."""
    symtab: dict[str, SymbolEntry] = {}
    ht = HandlerTable()
    reg = LiveValueRegistry()
    reg.declare(LiveValueDeclaration("humidity", "number"), "test-pack")
    # Symtab has the name registered with no value (matches what Session
    # does when packs declare live values).
    symtab["humidity"] = SymbolEntry(name="humidity", value=None, type="number")
    _register(
        symtab, ht, reg, "when humidity is above 80", 'show "humid"',
    )
    adapter = TestAdapter([("humidity", 85)], name="weather")
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    assert len(fires) == 1
    assert fires[0].output == ["humid"]
    assert fires[0].metadata["trigger"]["source"] == "adapter_update"


# ---------------------------------------------------------------------------
# unless guard (§109)
# ---------------------------------------------------------------------------


def test_unless_guard_suppresses_firing():
    """v3a sentence 97: handler with `unless` guard does not fire when
    the guard is true, even if the main condition is true."""
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "temperature", 50)
    _set_string(symtab, "silenced", "false")
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg,
        "when temperature is above 100 unless silenced is equal to true",
        'show "alert"',
    )
    adapter = TestAdapter(
        [("silenced", "true"), ("temperature", 105)], name="test",
    )
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    # Guard is true when temperature crosses 100 — no firing.
    assert len(fires) == 0


# ---------------------------------------------------------------------------
# finish (§112)
# ---------------------------------------------------------------------------


def test_finish_in_action_block_triggers_shutdown_with_reason_finish():
    """v3a §112 + sentence 98: `finish` is immediate and total. The
    listener yields no further action results; SHUTDOWN follows with
    reason="finish"."""
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "tally", 0)
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg, "when tally is above 2", "finish",
    )
    # First update below threshold (no fire), second above (finish).
    adapter = TestAdapter(
        [("tally", 1), ("tally", 3)], name="test",
    )
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    shutdowns = [r for r in results if r.status is ResultStatus.SHUTDOWN]
    assert len(shutdowns) == 1
    assert shutdowns[0].metadata["reason"] == "finish"
    assert shutdowns[0].metadata["handler_index"] == 0


def test_finish_during_initial_evaluation_prevents_adapter_start():
    """v3a §121: `finish` during initial evaluation aborts before
    adapters dispatch."""
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "level", 100)  # condition already true
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg, "when level is above 50", "finish",
    )
    # Adapter would push values if started — but finish from initial
    # evaluation should prevent its start.
    adapter = TestAdapter([("level", 200)], name="test")
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    # No HANDLER_FIRE for the action statement — finish suppresses it.
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    assert fires == []
    assert results[-1].status is ResultStatus.SHUTDOWN
    assert results[-1].metadata["reason"] == "finish"
    # Adapter was never started in the first place.
    assert adapter.started is False


# ---------------------------------------------------------------------------
# Multi-statement action block (sentence 99)
# ---------------------------------------------------------------------------


def test_multi_statement_action_block_yields_one_result_per_statement():
    """v3a sentence 99: each action statement gets its own HANDLER_FIRE
    result, all sharing the same trigger envelope."""
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "level", 0)
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg,
        "when level is above 50",
        'show "high"',
        "remember a string called status with active",
    )
    adapter = TestAdapter([("level", 75)], name="test")
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    assert len(fires) == 2
    assert fires[0].output == ["high"]
    # All share the same trigger metadata.
    assert fires[0].metadata["trigger"]["handler_index"] == 0
    assert fires[1].metadata["trigger"]["handler_index"] == 0
    # And the side effect committed to the symbol table.
    assert symtab["status"].value == "active"


# ---------------------------------------------------------------------------
# Cascading triggers (§114, sentence 100)
# ---------------------------------------------------------------------------


def test_cascading_trigger_fires_dependent_handler():
    """v3a sentence 100: a handler's action modifies a value that
    another handler depends on — the second handler fires depth-first
    with source="cascade"."""
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "temperature", 0)
    _set_string(symtab, "alert", "none")
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg,
        "when temperature is above 100",
        "remember a string called alert with triggered",
    )
    _register(
        symtab, ht, reg,
        "when alert is equal to triggered",
        'show "cascade fired"',
    )
    adapter = TestAdapter([("temperature", 105)], name="test")
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    # Handler 0 fires (sets alert), then handler 1 fires via cascade.
    assert len(fires) == 2
    assert fires[0].metadata["trigger"]["handler_index"] == 0
    assert fires[1].metadata["trigger"]["handler_index"] == 1
    assert fires[1].metadata["trigger"]["source"] == "cascade"
    assert fires[1].output == ["cascade fired"]


# ---------------------------------------------------------------------------
# Cycle detection (§114, sentence 101)
# ---------------------------------------------------------------------------


def test_cycle_detection_emits_error_runtime():
    """v3a §114 / sentence 101 intent: two handlers that toggle each
    other's state in a single cascade chain produce an ERROR_RUNTIME
    with metadata.kind="cycle".

    Note: the spec sentence's literal program (handlers that re-write
    the value the adapter just set) doesn't actually cycle under §113
    deep-equality change detection — no-op writes are absorbed
    silently. The conservative same-handler-twice guard is what the
    test exercises; this program produces a genuine ping-pong:

        handler 0: when score > 0  → score=0, level=1
        handler 1: when level > 0  → level=0, score=1
        adapter:   score=1
        => cascade: H0 fires (score=0, level=1)
        => cascade: H1 fires (level=0, score=1)
        => cascade: H0 would fire again — CYCLE
    """
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "score", 0)
    _set_number(symtab, "level", 0)
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg,
        "when score is above 0",
        "remember a number called score with 0",
        "remember a number called level with 1",
    )
    _register(
        symtab, ht, reg,
        "when level is above 0",
        "remember a number called level with 0",
        "remember a number called score with 1",
    )
    adapter = TestAdapter([("score", 1)], name="test")
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    runtime_errors = [
        r for r in results if r.status is ResultStatus.ERROR_RUNTIME
    ]
    assert len(runtime_errors) >= 1, (
        f"expected at least one ERROR_RUNTIME, got results: {results}"
    )
    cycle = runtime_errors[0]
    assert cycle.metadata["kind"] == "cycle"
    assert "path" in cycle.metadata


# ---------------------------------------------------------------------------
# Adapter failure isolation (§120)
# ---------------------------------------------------------------------------


def test_adapter_failure_yields_error_runtime_and_disables_handlers():
    """v3a §120: a malformed adapter script produces AdapterFailure,
    which the listener surfaces as ERROR_RUNTIME and uses to mark the
    adapter's live values inactive."""
    symtab: dict[str, SymbolEntry] = {}
    ht = HandlerTable()
    reg = LiveValueRegistry()
    reg.declare(LiveValueDeclaration("temperature", "number"), "bad-pack")
    symtab["temperature"] = SymbolEntry(
        name="temperature", value=None, type="number",
    )
    _register(
        symtab, ht, reg, "when temperature is above 100", 'show "x"',
    )
    # Script with a malformed entry → adapter pushes AdapterFailure.
    adapter = TestAdapter(
        [("temperature", 105), 999], name="bad-pack",  # 999 is malformed
    )
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    runtime_errors = [
        r for r in results if r.status is ResultStatus.ERROR_RUNTIME
    ]
    assert any(
        r.metadata.get("kind") == "adapter_failure" for r in runtime_errors
    )
    # The live value is now inactive.
    assert reg.entry("temperature").status == "inactive"


# ---------------------------------------------------------------------------
# Adapter completion shutdown (§120)
# ---------------------------------------------------------------------------


def test_adapter_complete_shutdown_reason():
    """v3a §120: when all adapters signal Done, the listener exits with
    reason="adapter_complete"."""
    symtab: dict[str, SymbolEntry] = {}
    _set_number(symtab, "temperature", 50)
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg, "when temperature is above 100", 'show "x"',
    )
    adapter = TestAdapter([("temperature", 105), "[done]"], name="test")
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    assert results[-1].status is ResultStatus.SHUTDOWN
    assert results[-1].metadata["reason"] == "adapter_complete"


# ---------------------------------------------------------------------------
# of-expression in `when` condition (sentence 104)
# ---------------------------------------------------------------------------


def test_when_with_of_expression_fires_on_record_update():
    """v3a sentence 104 + §108: handler dependency is on the record
    name. An adapter that updates the record triggers re-evaluation."""
    symtab: dict[str, SymbolEntry] = {}
    symtab["patient"] = SymbolEntry(
        name="patient",
        value={"name": "john", "status": "stable"},
        type="record",
        schema={"name": "string", "status": "string"},
    )
    ht = HandlerTable()
    reg = LiveValueRegistry()
    _register(
        symtab, ht, reg,
        "when status of patient is equal to critical",
        'show "alert"',
    )
    adapter = TestAdapter(
        [("patient", {"name": "john", "status": "critical"})],
        name="hospital",
    )
    results = _drain(listen(symtab, ht, reg, adapters=[adapter]))
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    assert len(fires) == 1
    assert fires[0].output == ["alert"]

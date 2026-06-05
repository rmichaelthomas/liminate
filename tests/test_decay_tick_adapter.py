"""Phase 4 D-7 — timer-driven decay.

The listener advances metabolic decay (`weakens X over N`) once per
`tick`-named adapter update, after the normal handler cascade for that tick
completes. No other adapter update triggers decay. Tests drive the listener
deterministically with a scripted TestDomainPack rather than the threaded
timer pack.
"""

from __future__ import annotations

from liminate.adapter import TestDomainPack
from liminate.result import ResultStatus
from liminate.vocabulary import DecayingValue

from tests._v3a_helpers import run_v3a


def _tick_pack(n_ticks: int, *, extra_decls=None):
    """A TestDomainPack that emits `tick` updates valued 1..n_ticks."""
    decls = [("tick", "number")]
    if extra_decls:
        decls.extend(extra_decls)
    return TestDomainPack(
        declarations=decls,
        script=[("tick", i) for i in range(1, n_ticks + 1)],
    )


def _outputs(results):
    return [line for r in results if r and r.output for line in r.output]


# ---------------------------------------------------------------------------
# 1–2 — decay advances on each tick
# ---------------------------------------------------------------------------


def test_decay_reaches_zero_over_its_period():
    """1. `weakens trust over 5` with 5 ticks decays trust to 0."""
    session, _ = run_v3a(
        """
        remember a number called trust with 100
        weakens trust over 5
        when trust is below 1
          show "gone"
        """,
        pack=_tick_pack(5),
    )
    decaying = session.symtab["trust"].value
    assert isinstance(decaying, DecayingValue)
    assert decaying.ticks_elapsed == 5
    assert decaying.current_value == 0.0


def test_decay_is_linear_per_tick():
    """2. After 3 of 5 ticks, trust is at 40% of its initial value."""
    session, _ = run_v3a(
        """
        remember a number called trust with 100
        weakens trust over 5
        when trust is below 1
          show "gone"
        """,
        pack=_tick_pack(3),
    )
    decaying = session.symtab["trust"].value
    assert decaying.ticks_elapsed == 3
    assert decaying.current_value == 40.0


# ---------------------------------------------------------------------------
# 3 — a when handler fires on decay
# ---------------------------------------------------------------------------


def test_handler_fires_when_decay_crosses_threshold():
    """3. `when trust is below 50` fires once decay brings trust under 50
    (at tick 3: 100 → 40)."""
    session, results = run_v3a(
        """
        remember a number called trust with 100
        weakens trust over 5
        when trust is below 50
          show "trust low"
        """,
        pack=_tick_pack(5),
    )
    fires = [r for r in results if r.status is ResultStatus.HANDLER_FIRE]
    assert fires
    assert any("trust low" in line for line in _outputs(results))


# ---------------------------------------------------------------------------
# 4 — non-tick updates do not advance decay
# ---------------------------------------------------------------------------


def test_non_tick_update_does_not_advance_decay():
    """4. A `temperature` update from another source must not tick decay."""
    pack = TestDomainPack(
        declarations=[("tick", "number"), ("temperature", "number")],
        script=[("temperature", 20), ("temperature", 21)],
    )
    session, _ = run_v3a(
        """
        remember a number called trust with 100
        weakens trust over 5
        when temperature is above 100
          show "hot"
        """,
        pack=pack,
    )
    decaying = session.symtab["trust"].value
    assert decaying.ticks_elapsed == 0
    assert decaying.current_value == 100.0


# ---------------------------------------------------------------------------
# 5 — multiple decaying values advance together
# ---------------------------------------------------------------------------


def test_multiple_decaying_values_advance_each_tick():
    """5. Two decaying values with different periods both advance per tick."""
    session, _ = run_v3a(
        """
        remember a number called trust with 100
        remember a number called confidence with 100
        weakens trust over 5
        weakens confidence over 10
        when trust is below 1
          show "gone"
        """,
        pack=_tick_pack(5),
    )
    trust = session.symtab["trust"].value
    confidence = session.symtab["confidence"].value
    assert trust.ticks_elapsed == 5
    assert confidence.ticks_elapsed == 5
    assert trust.current_value == 0.0       # 100 - 20*5
    assert confidence.current_value == 50.0  # 100 - 10*5


# ---------------------------------------------------------------------------
# 6 — reinforcement mid-decay resets
# ---------------------------------------------------------------------------


def test_reinforcement_mid_decay_resets():
    """6. Re-remembering trust in a tick-3 handler reinforces (resets) the
    decay in place. The handler fires before that tick's decay advance, so
    after the reset ticks 3, 4 and 5 each advance decay once."""
    session, results = run_v3a(
        """
        remember a number called trust with 100
        weakens trust over 5
        when tick is equal to 3
          remember a number called trust with 100
        """,
        pack=_tick_pack(5),
    )
    decaying = session.symtab["trust"].value
    # Reset (ticks_elapsed → 0) happened inside tick 3, before its decay
    # advance; ticks 3, 4 and 5 then advanced decay → ticks_elapsed == 3.
    assert isinstance(decaying, DecayingValue)
    assert decaying.initial_value == 100.0
    assert decaying.ticks_elapsed == 3
    assert decaying.current_value == 40.0  # 100 - 20*3


# ---------------------------------------------------------------------------
# 7 — finish during a decay-triggered handler stops cleanly
# ---------------------------------------------------------------------------


def test_finish_during_decay_handler_stops_listener():
    """7. `finish` inside a handler that fired due to decay stops the
    listener cleanly (a SHUTDOWN result, no errors)."""
    session, results = run_v3a(
        """
        remember a number called trust with 100
        weakens trust over 5
        when trust is below 50
          finish
        """,
        pack=_tick_pack(5),
    )
    assert any(r.status is ResultStatus.SHUTDOWN for r in results)
    assert not any(
        r.status in (ResultStatus.ERROR_RUNTIME, ResultStatus.ERROR_SEMANTIC)
        for r in results
    )


# ---------------------------------------------------------------------------
# 8 — no decaying values: tick_decay is a no-op
# ---------------------------------------------------------------------------


def test_no_decaying_values_is_noop():
    """8. With no `weakens`, ticks fire handlers but tick_decay does nothing
    and raises nothing."""
    session, results = run_v3a(
        """
        remember a number called seen with 0
        when tick is equal to 2
          show "tick two"
        """,
        pack=_tick_pack(3),
    )
    assert any("tick two" in line for line in _outputs(results))
    assert not any(
        r.status in (ResultStatus.ERROR_RUNTIME, ResultStatus.ERROR_SEMANTIC)
        for r in results
    )


# ---------------------------------------------------------------------------
# 9 — decay reaching zero fires a watcher for zero
# ---------------------------------------------------------------------------


def test_decay_reaching_zero_fires_zero_watcher():
    """9. A handler watching for the floor fires when decay hits 0."""
    session, results = run_v3a(
        """
        remember a number called trust with 100
        weakens trust over 5
        when trust is equal to 0
          show "depleted"
        """,
        pack=_tick_pack(5),
    )
    assert session.symtab["trust"].value.current_value == 0.0
    assert any("depleted" in line for line in _outputs(results))


# ---------------------------------------------------------------------------
# 10 — full integration: scripted timer + decay + cascade
# ---------------------------------------------------------------------------


def test_integration_timer_decay_and_cascade():
    """10. End to end: ticks drive decay, the decay crossing fires a handler,
    and the listener shuts down normally."""
    session, results = run_v3a(
        """
        remember a number called trust with 100
        weakens trust over 4
        when trust is below 50
          show "below half"
        """,
        pack=_tick_pack(4),
    )
    statuses = [r.status for r in results]
    assert ResultStatus.LISTENING in statuses
    assert ResultStatus.HANDLER_FIRE in statuses
    assert ResultStatus.SHUTDOWN in statuses
    assert session.symtab["trust"].value.current_value == 0.0
    assert any("below half" in line for line in _outputs(results))

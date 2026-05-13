"""Tests for the timer domain pack (src/inscript/packs/timer.py).

The timer pack is the first non-test domain pack — it exercises the
v3a §116–§120 adapter contract with real threading. Intervals in
these tests are kept short (≤50 ms) so the suite stays fast.
"""

from __future__ import annotations

import time
from queue import Empty, Queue

import pytest

from inscript.adapter import AdapterDone, AdapterUpdate, LiveValueDeclaration
from inscript.packs.timer import TimerAdapter, TimerDomainPack


# ---------------------------------------------------------------------------
# Declarations
# ---------------------------------------------------------------------------


def test_timer_pack_declares_tick_and_elapsed_as_numbers():
    pack = TimerDomainPack()
    decls = pack.declarations()
    by_name = {d.name: d for d in decls}
    assert set(by_name) == {"tick", "elapsed"}
    assert by_name["tick"] == LiveValueDeclaration(name="tick", value_type="number")
    assert by_name["elapsed"] == LiveValueDeclaration(name="elapsed", value_type="number")


def test_timer_pack_name_defaults_to_timer():
    assert TimerDomainPack().name() == "timer"


def test_timer_adapter_rejects_non_positive_interval():
    with pytest.raises(ValueError) as exc:
        TimerAdapter(interval_ms=0)
    assert "interval_ms" in str(exc.value)


def test_timer_adapter_rejects_negative_max_ticks():
    with pytest.raises(ValueError) as exc:
        TimerAdapter(max_ticks=-1)
    assert "max_ticks" in str(exc.value)


def test_timer_pack_validates_args_at_construction():
    """TimerDomainPack(interval_ms=-1) must fail immediately, not at
    later adapter() time — otherwise the error surfaces far from its
    cause."""
    with pytest.raises(ValueError):
        TimerDomainPack(interval_ms=-1)
    with pytest.raises(ValueError):
        TimerDomainPack(max_ticks=-1)


def test_timer_pack_adapter_is_cached():
    pack = TimerDomainPack()
    a1 = pack.adapter()
    a2 = pack.adapter()
    assert a1 is a2


# ---------------------------------------------------------------------------
# Adapter behavior
# ---------------------------------------------------------------------------


def _drain_until_done(q: Queue, *, timeout: float = 2.0) -> list:
    """Drain the queue until an AdapterDone arrives or `timeout` elapses."""
    out: list = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            msg = q.get(timeout=0.05)
        except Empty:
            continue
        out.append(msg)
        if isinstance(msg, AdapterDone):
            return out
    return out


def test_timer_adapter_emits_tick_sequence_up_to_max_ticks():
    """max_ticks=3 produces exactly three (tick, N) updates with values
    1, 2, 3 (plus matching elapsed updates and a terminal AdapterDone)."""
    q: Queue = Queue()
    adapter = TimerAdapter(interval_ms=20, max_ticks=3)
    adapter.attach_queue(q)
    adapter.start()
    events = _drain_until_done(q)

    tick_updates = [
        e for e in events if isinstance(e, AdapterUpdate) and e.name == "tick"
    ]
    assert [u.value for u in tick_updates] == [1, 2, 3]

    elapsed_updates = [
        e for e in events if isinstance(e, AdapterUpdate) and e.name == "elapsed"
    ]
    assert len(elapsed_updates) == 3
    for u in elapsed_updates:
        assert isinstance(u.value, float)

    # AdapterDone is the final event, exactly once.
    done = [e for e in events if isinstance(e, AdapterDone)]
    assert len(done) == 1
    assert events[-1] is done[0]
    assert done[0].adapter_name == "timer"

    # Defensive: thread must join cleanly (stop() handles join).
    adapter.stop()


def test_timer_adapter_start_without_queue_raises():
    adapter = TimerAdapter(interval_ms=20, max_ticks=1)
    with pytest.raises(RuntimeError):
        adapter.start()

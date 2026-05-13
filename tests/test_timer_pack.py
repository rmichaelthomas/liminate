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


def test_timer_adapter_stops_cleanly_mid_run():
    """Calling stop() while the timer is mid-run must:
      - terminate the background thread within ~stop-grace,
      - leave the queue with at most max_ticks (tick, _) updates,
      - NOT emit AdapterDone (stop is external, not natural).
    """
    q: Queue = Queue()
    # No max_ticks → would run forever. We stop after letting it
    # produce ~1–2 ticks.
    adapter = TimerAdapter(interval_ms=20, max_ticks=None)
    adapter.attach_queue(q)
    adapter.start()
    time.sleep(0.05)  # ~2 ticks of headroom
    adapter.stop()

    # Thread joined cleanly.
    assert adapter._thread is not None
    assert not adapter._thread.is_alive()
    assert adapter.stopped is True

    # Drain remaining events; verify no AdapterDone slipped in (stop
    # is external; only natural max_ticks completion emits Done).
    events: list = []
    while not q.empty():
        events.append(q.get_nowait())
    assert not any(isinstance(e, AdapterDone) for e in events)


def test_timer_adapter_stop_interrupts_pending_interval():
    """stop() must wake a long sleep promptly — the threading.Event-
    based interruptible sleep is the whole reason this adapter does
    not use time.sleep(). A regression here would silently break
    `finish` semantics under v3a §112."""
    q: Queue = Queue()
    # Long interval, no max_ticks: would block 10s without interruption.
    adapter = TimerAdapter(interval_ms=10_000)
    adapter.attach_queue(q)
    adapter.start()
    t0 = time.monotonic()
    adapter.stop()
    elapsed = time.monotonic() - t0
    assert elapsed < 0.5, f"stop() took {elapsed:.3f}s — not interruptible"
    assert adapter._thread is not None
    assert not adapter._thread.is_alive()


def test_timer_adapter_stop_is_idempotent():
    q: Queue = Queue()
    adapter = TimerAdapter(interval_ms=20, max_ticks=2)
    adapter.attach_queue(q)
    adapter.start()
    adapter.stop()
    adapter.stop()  # second call must not raise
    assert adapter.stopped is True


def test_timer_adapter_elapsed_is_monotonically_non_decreasing():
    """`elapsed` is rounded to 1 decimal place, so equal-to-previous
    values are legal (two ticks may land in the same 100ms bucket at
    short intervals). Strictly: each value >= the previous."""
    q: Queue = Queue()
    adapter = TimerAdapter(interval_ms=30, max_ticks=5)
    adapter.attach_queue(q)
    adapter.start()
    events = _drain_until_done(q)
    adapter.stop()

    elapsed_values = [
        e.value for e in events
        if isinstance(e, AdapterUpdate) and e.name == "elapsed"
    ]
    assert len(elapsed_values) == 5
    for prev, cur in zip(elapsed_values, elapsed_values[1:]):
        assert cur >= prev, f"elapsed went backwards: {prev} -> {cur}"
    # Sanity check: last elapsed is within a reasonable window.
    assert elapsed_values[-1] < 5.0  # 5 ticks * 30ms < 200ms, well under 5s


# ---------------------------------------------------------------------------
# Factory + CLI integration
# ---------------------------------------------------------------------------


def test_make_timer_pack_reads_config_fields():
    from inscript.packs.timer import make_timer_pack

    pack = make_timer_pack({
        "interval_ms": 75,
        "max_ticks": 4,
        "name": "ticker",
    })
    assert isinstance(pack, TimerDomainPack)
    assert pack.name() == "ticker"
    adapter = pack.adapter()
    assert isinstance(adapter, TimerAdapter)
    assert adapter.interval_ms == 75
    assert adapter.max_ticks == 4


def test_make_timer_pack_defaults_are_sensible():
    from inscript.packs.timer import make_timer_pack

    pack = make_timer_pack({})
    adapter = pack.adapter()
    assert adapter.interval_ms == 1000  # _DEFAULT_INTERVAL_MS
    assert adapter.max_ticks is None  # run forever by default


def test_make_timer_pack_rejects_unknown_keys():
    from inscript.packs.timer import make_timer_pack

    with pytest.raises(ValueError) as exc:
        make_timer_pack({"interval_ms": 100, "wat": 1})
    assert "wat" in str(exc.value)


def test_load_pack_from_arg_inline_timer():
    from inscript.cli import load_pack_from_arg

    pack = load_pack_from_arg(
        '{"type": "timer", "interval_ms": 50, "max_ticks": 2}'
    )
    assert pack.name() == "timer"
    decls = {d.name for d in pack.declarations()}
    assert decls == {"tick", "elapsed"}


def test_load_pack_from_arg_inline_test_default_type():
    """Configs without a `"type"` key remain TestDomainPack — preserves
    backward compatibility with existing dogfood pack JSON files."""
    from inscript.cli import load_pack_from_arg

    pack = load_pack_from_arg(
        '{"declarations": [["x", "number"]], "script": [["x", 1], "[done]"]}'
    )
    assert {d.name for d in pack.declarations()} == {"x"}


def test_load_pack_from_arg_file_path_still_works(tmp_path):
    """Regression: existing dogfood JSON files (no `"type"` field) load
    as TestDomainPack."""
    import json
    from inscript.cli import load_pack_from_arg

    p = tmp_path / "pack.json"
    p.write_text(json.dumps({
        "name": "weather",
        "declarations": [["temperature", "number"]],
        "script": [["temperature", 100], "[done]"],
    }))
    pack = load_pack_from_arg(str(p))
    assert pack.name() == "weather"


def test_load_pack_from_arg_unknown_type_raises():
    from inscript.cli import load_pack_from_arg

    with pytest.raises(ValueError) as exc:
        load_pack_from_arg('{"type": "no-such-pack"}')
    assert "no-such-pack" in str(exc.value)


# ---------------------------------------------------------------------------
# Integration: timer updates flow through the listener and fire handlers
# ---------------------------------------------------------------------------


def test_timer_pack_drives_when_handler_through_listener():
    """A `when tick is above 2` handler must fire exactly once when
    the timer pack pushes tick=3 (edge-triggered, v3a §113). `finish`
    yields SHUTDOWN with reason="finish", and the post-handler symtab
    reflects the action.

    Uses a short interval (20ms) and max_ticks=4 so the test
    completes in <200ms even on slow CI machines.
    """
    from tests._v3a_helpers import run_v3a, fires
    from inscript.result import ResultStatus

    pack = TimerDomainPack(interval_ms=20, max_ticks=4)
    session, results = run_v3a(
        """
        remember a string called status with waiting

        when tick is above 2
          remember a string called status with crossed
          finish
        """,
        pack=pack,
    )

    handler_fires = fires(results)
    shutdowns = [r for r in results if r.status is ResultStatus.SHUTDOWN]

    assert len(handler_fires) == 1
    assert shutdowns and shutdowns[-1].metadata == {
        "reason": "finish", "handler_index": 0,
    }
    assert session.symtab["status"].value == "crossed"

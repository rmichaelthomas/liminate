"""Timer domain pack — periodic ticks as a live event source.

v3a §116 — declarations + adapter. v3a §119 — single-threaded event
queue (adapter pushes only; never reads). v3a §120 — `stop()` is
interruptible so `finish` and external shutdown don't block on the
sleep interval.

Declarations
------------
- `tick`    — number; increments by 1 every `interval_ms`. Starts at 1
              on the first push (live values are `unset` until the
              first update per v3a §117).
- `elapsed` — number; seconds since adapter start, rounded to 1
              decimal place. Updated on every tick.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from ..adapter import (
    Adapter,
    AdapterDone,
    AdapterUpdate,
    DomainPack,
    LiveValueDeclaration,
)


_DEFAULT_INTERVAL_MS = 1000


def _validate_timer_args(interval_ms: int, max_ticks: int | None) -> None:
    if interval_ms <= 0:
        raise ValueError(
            f"TimerAdapter interval_ms must be positive (got {interval_ms})."
        )
    if max_ticks is not None and max_ticks < 0:
        raise ValueError(
            f"TimerAdapter max_ticks must be >= 0 or None (got {max_ticks})."
        )


class TimerAdapter(Adapter):
    """Real adapter implementation — runs on a background thread.

    The thread loop sleeps via `threading.Event.wait(timeout)` so
    `stop()` can interrupt the sleep without waiting for the full
    interval. The interpreter's listener calls `stop()` on `finish`
    (v3a §112) and at shutdown (§120); both paths must return
    promptly.
    """

    def __init__(
        self,
        *,
        interval_ms: int = _DEFAULT_INTERVAL_MS,
        max_ticks: int | None = None,
        name: str = "timer",
    ) -> None:
        super().__init__(name=name)
        _validate_timer_args(interval_ms, max_ticks)
        self.interval_ms = interval_ms
        self.max_ticks = max_ticks
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self.queue is None:
            raise RuntimeError(
                "TimerAdapter.start() called before attach_queue()."
            )
        if self.started:
            return
        self.started = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name=f"{self.name}-thread",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        # Idempotent: repeated calls (listener-shutdown + atexit, etc.)
        # are safe.
        if self.stopped:
            return
        self.stopped = True
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)

    def _run(self) -> None:
        """Background-thread loop. Pushes (tick, N) and (elapsed, S)
        pairs every `interval_ms`. On `max_ticks` reached, pushes one
        terminal `AdapterDone` and exits the thread.

        On `stop()` (always invoked from the listener itself — see
        the Adapter contract), `_stop_event` is set; the thread
        exits without pushing `AdapterDone`. The listener has
        already decided to shut down by the time stop() is called,
        so the missing terminal signal is intentional."""
        interval_s = self.interval_ms / 1000.0
        start_time = time.monotonic()
        tick_count = 0
        while not self._stop_event.is_set():
            # Interruptible sleep: wait() returns True if the event
            # is set during the wait.
            if self._stop_event.wait(timeout=interval_s):
                return
            tick_count += 1
            elapsed = round(time.monotonic() - start_time, 1)
            self.queue.put(AdapterUpdate(name="tick", value=tick_count))
            self.queue.put(AdapterUpdate(name="elapsed", value=elapsed))
            if self.max_ticks is not None and tick_count >= self.max_ticks:
                self.queue.put(AdapterDone(adapter_name=self.name))
                return


class TimerDomainPack(DomainPack):
    """DomainPack wrapper around a TimerAdapter."""

    def __init__(
        self,
        *,
        interval_ms: int = _DEFAULT_INTERVAL_MS,
        max_ticks: int | None = None,
        name: str = "timer",
    ) -> None:
        _validate_timer_args(interval_ms, max_ticks)
        self._name = name
        self._interval_ms = interval_ms
        self._max_ticks = max_ticks
        self._adapter: TimerAdapter | None = None

    def name(self) -> str:
        return self._name

    def declarations(self) -> list[LiveValueDeclaration]:
        return [
            LiveValueDeclaration(name="tick", value_type="number"),
            LiveValueDeclaration(name="elapsed", value_type="number"),
        ]

    def adapter(self) -> Adapter:
        if self._adapter is None:
            self._adapter = TimerAdapter(
                interval_ms=self._interval_ms,
                max_ticks=self._max_ticks,
                name=self._name,
            )
        return self._adapter


_TIMER_CONFIG_KEYS = {"interval_ms", "max_ticks", "name"}


def make_timer_pack(config: dict[str, Any]) -> TimerDomainPack:
    """Factory used by the CLI `--pack` flag when `type == "timer"`.

    Accepts a dict (typically decoded from JSON) with optional keys:
      - `interval_ms`: int, default 1000.
      - `max_ticks`:   int or null, default null (run forever).
      - `name`:        str, default "timer".
    Unknown keys raise — typos shouldn't silently produce a default
    pack."""
    extra = set(config) - _TIMER_CONFIG_KEYS - {"type"}
    if extra:
        raise ValueError(
            f"timer pack config has unknown key(s): {sorted(extra)}. "
            f"Allowed: {sorted(_TIMER_CONFIG_KEYS)}."
        )
    return TimerDomainPack(
        interval_ms=int(config.get("interval_ms", _DEFAULT_INTERVAL_MS)),
        max_ticks=(
            int(config["max_ticks"])
            if config.get("max_ticks") is not None
            else None
        ),
        name=str(config.get("name", "timer")),
    )

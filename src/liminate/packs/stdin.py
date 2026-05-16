"""Stdin reader domain pack — each line of stdin becomes a live update.

Follows the v3a §116–§120 adapter contract: a background thread reads
`sys.stdin.readline()` in a loop and pushes each line as an
`AdapterUpdate(name="line", value=<stripped line>)`. EOF (readline
returning the empty string) signals normal adapter completion via
`AdapterDone`.

Declarations
------------
- `line` — string; the most recently read line, trailing newline
            stripped. Whitespace-only lines are still pushed verbatim —
            only true EOF signals completion.

Notes
-----
- v3a §113 is edge-triggered with deep value equality: two identical
  consecutive lines will produce one update but only the first will
  re-fire any handler watching `line` (the second is not a
  false→true transition). This is correct behavior, not a bug.
- `sys.stdin.readline()` is a blocking syscall on most platforms.
  `stop()` sets a flag but cannot interrupt a pending readline; the
  background thread is therefore a daemon so process exit isn't
  blocked. Subsequent input arrival (or EOF) wakes the thread, it
  notices the stop flag, and exits cleanly.
"""

from __future__ import annotations

import sys
import threading
from typing import Any, TextIO

from ..adapter import (
    Adapter,
    AdapterDone,
    AdapterUpdate,
    DomainPack,
    LiveValueDeclaration,
)


class StdinAdapter(Adapter):
    """Background-thread adapter reading lines from a text stream."""

    def __init__(
        self,
        *,
        name: str = "stdin",
        stream: TextIO | None = None,
    ) -> None:
        super().__init__(name=name)
        self._stream = stream  # resolved at start() to allow late sys.stdin swaps
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self.queue is None:
            raise RuntimeError(
                "StdinAdapter.start() called before attach_queue()."
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
        if self.stopped:
            return
        self.stopped = True
        self._stop_event.set()
        # We can't reliably interrupt sys.stdin.readline() across platforms.
        # The thread is daemonic; give it a brief join window in case stdin
        # is a closable in-memory stream (tests), then move on.
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=0.1)

    def _run(self) -> None:
        stream = self._stream if self._stream is not None else sys.stdin
        while not self._stop_event.is_set():
            try:
                raw = stream.readline()
            except Exception:
                # Stream closed or broken — signal done and exit.
                self.queue.put(AdapterDone(adapter_name=self.name))
                return
            if raw == "":
                # True EOF.
                self.queue.put(AdapterDone(adapter_name=self.name))
                return
            if self._stop_event.is_set():
                return
            # Strip only the trailing newline characters; preserve
            # interior whitespace and trailing spaces within the line.
            line = raw.rstrip("\r\n")
            self.queue.put(AdapterUpdate(name="line", value=line))


class StdinDomainPack(DomainPack):
    """DomainPack wrapping a StdinAdapter."""

    def __init__(
        self,
        *,
        name: str = "stdin",
        stream: TextIO | None = None,
    ) -> None:
        self._name = name
        self._stream = stream
        self._adapter: StdinAdapter | None = None

    def name(self) -> str:
        return self._name

    def declarations(self) -> list[LiveValueDeclaration]:
        return [LiveValueDeclaration(name="line", value_type="string")]

    def adapter(self) -> Adapter:
        if self._adapter is None:
            self._adapter = StdinAdapter(name=self._name, stream=self._stream)
        return self._adapter


_STDIN_CONFIG_KEYS = {"name"}


def make_stdin_pack(config: dict[str, Any]) -> StdinDomainPack:
    """Factory used by the CLI `--pack` flag when `type == "stdin"`.

    Accepts optional keys:
      - `name`: str, default "stdin".
    Unknown keys raise — typos shouldn't silently produce a default
    pack."""
    extra = set(config) - _STDIN_CONFIG_KEYS - {"type"}
    if extra:
        raise ValueError(
            f"stdin pack config has unknown key(s): {sorted(extra)}. "
            f"Allowed: {sorted(_STDIN_CONFIG_KEYS)}."
        )
    return StdinDomainPack(name=str(config.get("name", "stdin")))

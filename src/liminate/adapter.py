"""Adapter infrastructure for Liminate v3a event-driven execution.

Sources:
- v3a §116 (event sources: adapter contract — declaration, adapter, lifecycle)
- v3a §117 (live value lifecycle: declared → unset → active → inactive)
- v3a §118 (domain pack registration via constructor/CLI, not language syntax)
- v3a §119 (single-threaded event queue: adapters enqueue; interpreter
  processes one update to completion before next dequeue)
- v3a §120 (adapter failure isolation: single crash doesn't kill the
  interpreter; dependent handlers disable; queue keeps draining)

This module defines the contract by which external event sources (domain
packs) feed the Phase 2 reactive interpreter. v3a ships exactly one
adapter implementation: `TestAdapter`, used by integration tests and the
dogfood program. Real-world domain packs (healthcare, smart home, game)
are explicitly out of scope (§126).

The interpreter owns the event queue and the live-value registry; each
adapter contributes updates and declarations. Adapters never read from
the queue themselves — they only push.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from queue import Queue
from typing import Any

from .vocabulary import (
    PackVerbExecution,
    PackVerbSignature,
    PackVerbSlot,
)


# ---------------------------------------------------------------------------
# Declarations and queue messages (§116)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LiveValueDeclaration:
    """A live value declared by a domain pack (§116).

    `value_type` matches the analyzer's type strings: "number", "string",
    "record", "list_of_numbers", "list_of_strings", "list_of_records".
    For broad declarations the adapter's first update establishes the
    final shape (§116).
    """
    name: str
    value_type: str


@dataclass
class AdapterUpdate:
    """A `(name, new_value)` pair pushed by an adapter (§119).

    The interpreter consumes one update at a time, runs change detection
    (§113 — deep value equality), and fires eligible handlers before
    dequeuing the next."""
    name: str
    value: Any


@dataclass
class AdapterDone:
    """Marker that an adapter has finished normally (§118 — "[done]"
    in test sentence notation). The interpreter counts these against
    the active-adapter set to decide when to shut down."""
    adapter_name: str


@dataclass
class AdapterFailure:
    """An adapter failure isolated to that adapter (§120). The
    interpreter marks the adapter's live values inactive and disables
    handlers that depend solely on them; other adapters keep running."""
    adapter_name: str
    reason: str


# ---------------------------------------------------------------------------
# Adapter and DomainPack ABCs (§116/§118)
# ---------------------------------------------------------------------------


class Adapter(ABC):
    """Adapter contract (§116).

    An adapter pushes `(name, value)` updates into a shared, thread-safe
    queue owned by the interpreter. Concrete adapters override `start`
    (begin pushing) and `stop` (cease pushing). `attach_queue` is called
    by the interpreter before `start` to wire up the queue.

    `name` is a human-readable identifier surfaced in error and
    shutdown metadata (§120 / §122).

    **Termination contract.** For the listener's Phase 2 drain loop to
    exit normally, every adapter must eventually push exactly one
    `AdapterDone(adapter_name=self.name)` (natural completion) or one
    `AdapterFailure(...)` (error). Adapters that run forever and never
    signal completion will keep the listener alive until the user's
    program calls `finish` (which triggers stop() from inside the
    listener) or the process is interrupted externally.

    `stop()` is invoked by the listener — either from `_shutdown_finish`
    after a `finish` propagates, or from the final cleanup loop after
    the drain has already returned. Concrete adapters should treat
    `stop()` as "cease pushing as soon as practical and tear down any
    threads or resources." They do not need to push a terminal
    `AdapterDone` from within `stop()` itself — by that point the
    listener has already decided to shut down.
    """

    def __init__(self, name: str = "adapter"):
        self.name = name
        self.queue: Queue | None = None
        self.started = False
        self.stopped = False

    def attach_queue(self, queue: Queue) -> None:
        """Called by the interpreter before `start`. The adapter
        uses `self.queue.put(...)` to enqueue updates from this point."""
        self.queue = queue

    @abstractmethod
    def start(self) -> None:
        """Begin pushing updates into the attached queue. Must not be
        called before `attach_queue`."""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """Cease pushing. Called by the interpreter on `finish` (§112),
        on global completion (§120), or on external termination."""
        raise NotImplementedError


class DomainPack(ABC):
    """Domain pack contract (§118).

    A pack groups one or more live value declarations with the adapter
    that produces them. Packs are registered with the interpreter at
    construction time — no Liminate-level `use`/`load` verb in v3a
    (§118).
    """

    @abstractmethod
    def name(self) -> str:
        """Human-readable identifier — used in error messages and
        shutdown metadata."""
        raise NotImplementedError

    @abstractmethod
    def declarations(self) -> list[LiveValueDeclaration]:
        """Return the live values this pack provides. The interpreter
        registers each name in the symbol table before Phase 1 begins
        (§116/§117)."""
        raise NotImplementedError

    @abstractmethod
    def adapter(self) -> Adapter:
        """Return the adapter that will push updates for this pack's
        declared live values."""
        raise NotImplementedError

    # v4a §137 — optional pack contributions to the active vocabulary.
    # Default to empty so existing packs (which override only the three
    # required methods above) keep working unchanged. Backward-compatible.

    def vocabulary(self) -> list[tuple[str, str]]:
        """Pack-contributed vocabulary as `(word, category)` pairs. v4a
        only consumes the noun category; other categories are reserved
        for future extension."""
        return []

    def verbs(self) -> list[PackVerbSignature]:
        """Pack-contributed verbs and their slot signatures (v4a §137).
        Empty by default."""
        return []


# ---------------------------------------------------------------------------
# v4a §137 — JSON pack verb deserialization helper
# ---------------------------------------------------------------------------


def parse_pack_verb_signature(definition: dict) -> PackVerbSignature:
    """Convert a single JSON `verbs[]` entry into a PackVerbSignature.

    The JSON schema (§137):
      {
        "word": "<verb-name>",
        "slots": [
          {"name": "...", "connective": "...", "required": true,
           "type_constraint": "..."}
        ],
        "execution": {"type": "set_value", "target_name": "...",
                      "source_slot": "..."}
      }
    """
    word = definition["word"]
    raw_slots = definition.get("slots", [])
    slots: list[PackVerbSlot] = []
    for s in raw_slots:
        slots.append(
            PackVerbSlot(
                name=s["name"],
                connective=s["connective"],
                required=bool(s.get("required", True)),
                type_constraint=s.get("type_constraint"),
            )
        )
    exec_def = definition.get("execution") or {}
    execution = PackVerbExecution(
        type=exec_def.get("type", ""),
        target_name=exec_def.get("target_name"),
        source_slot=exec_def.get("source_slot"),
    )
    return PackVerbSignature(
        word=word, slots=tuple(slots), execution=execution,
    )


# ---------------------------------------------------------------------------
# TestAdapter / TestDomainPack — the v3a-shipped test surface (§118)
# ---------------------------------------------------------------------------


class TestAdapter(Adapter):
    """Adapter that pushes a scripted, finite sequence of updates.

    The script is a list of items, each one of:
      - `("name", value)` — an `AdapterUpdate` push
      - `"[done]"`        — an explicit `AdapterDone` push

    `start()` drains the entire script onto the queue synchronously
    (single-threaded test semantics — the interpreter consumes them in
    order). If the script does not end with `"[done]"`, an
    `AdapterDone` is appended automatically so the interpreter sees
    normal completion (§118).

    `stop()` is idempotent — repeated calls are safe.
    """

    # pytest collects classes whose names begin with "Test" by default;
    # opt this Adapter implementation out so it isn't mistaken for a
    # test suite.
    __test__ = False

    def __init__(
        self,
        script: list[tuple[str, Any] | str],
        *,
        name: str = "test-adapter",
    ):
        super().__init__(name=name)
        self._script: list[tuple[str, Any] | str] = list(script)

    def start(self) -> None:
        if self.queue is None:
            raise RuntimeError(
                "TestAdapter.start() called before attach_queue()."
            )
        if self.started:
            return
        self.started = True
        ended_with_done = False
        for entry in self._script:
            if isinstance(entry, str) and entry == "[done]":
                self.queue.put(AdapterDone(adapter_name=self.name))
                ended_with_done = True
                continue
            if isinstance(entry, tuple) and len(entry) == 2:
                self.queue.put(
                    AdapterUpdate(name=entry[0], value=entry[1])
                )
                ended_with_done = False
                continue
            # Malformed script entry — surface as adapter failure so the
            # interpreter can isolate it (§120).
            self.queue.put(
                AdapterFailure(
                    adapter_name=self.name,
                    reason=f"malformed script entry: {entry!r}",
                )
            )
            return
        if not ended_with_done:
            # §118: every adapter must eventually signal normal
            # completion (or fail) for the interpreter to decide when
            # to shut down.
            self.queue.put(AdapterDone(adapter_name=self.name))

    def stop(self) -> None:
        self.stopped = True


class TestDomainPack(DomainPack):
    """DomainPack wrapping a TestAdapter and a fixed declaration list.

    Used by Phase 11 integration tests and the v3a dogfood program to
    drive event-driven sentences deterministically."""

    # pytest collects classes whose names begin with "Test" by default;
    # opt this DomainPack implementation out so it isn't mistaken for
    # a test suite.
    __test__ = False

    def __init__(
        self,
        declarations: list[tuple[str, str]] | list[LiveValueDeclaration],
        script: list[tuple[str, Any] | str],
        *,
        name: str = "test-pack",
        vocabulary: list[tuple[str, str]] | None = None,
        verbs: list[PackVerbSignature] | None = None,
    ):
        self._name = name
        self._declarations: list[LiveValueDeclaration] = [
            d if isinstance(d, LiveValueDeclaration)
            else LiveValueDeclaration(name=d[0], value_type=d[1])
            for d in declarations
        ]
        self._script = script
        self._adapter: TestAdapter | None = None
        self._vocabulary: list[tuple[str, str]] = list(vocabulary or [])
        self._verbs: list[PackVerbSignature] = list(verbs or [])

    def name(self) -> str:
        return self._name

    def declarations(self) -> list[LiveValueDeclaration]:
        return list(self._declarations)

    def adapter(self) -> Adapter:
        if self._adapter is None:
            self._adapter = TestAdapter(self._script, name=self._name)
        return self._adapter

    def vocabulary(self) -> list[tuple[str, str]]:
        return list(self._vocabulary)

    def verbs(self) -> list[PackVerbSignature]:
        return list(self._verbs)


# ---------------------------------------------------------------------------
# Live-value registry (§117)
# ---------------------------------------------------------------------------


@dataclass
class LiveValueEntry:
    """Per-live-value bookkeeping the interpreter consults during
    Phase 2 (§117).

    `status` transitions:
      unset    -> initial state; conditions involving this name
                  evaluate as false (§113).
      active   -> at least one value has been received (Phase 1 init
                  or first adapter update); conditions evaluate
                  normally.
      inactive -> the owning adapter failed (§117/§120); dependent
                  handlers are disabled.
    """
    name: str
    value_type: str
    adapter_name: str
    status: str = "unset"


class LiveValueRegistry:
    """Tracks which symbol-table names are adapter-owned and what
    state their adapter is in (§117/§120).

    Used by:
    - The analyzer (via `live_value_names`) to enforce ownership rules
      (§111: `remember`/`filter` restrictions).
    - The interpreter to update status on adapter updates and failures,
      and to disable handlers when adapters die.
    """

    def __init__(self) -> None:
        self._entries: dict[str, LiveValueEntry] = {}

    def declare(
        self, decl: LiveValueDeclaration, adapter_name: str,
    ) -> None:
        """Register a live value before Phase 1 (§117 step 1)."""
        if decl.name in self._entries:
            raise ValueError(
                f"live value '{decl.name}' was already declared by "
                f"'{self._entries[decl.name].adapter_name}' — v3a §116 "
                f"disallows multiple adapters providing the same name."
            )
        self._entries[decl.name] = LiveValueEntry(
            name=decl.name,
            value_type=decl.value_type,
            adapter_name=adapter_name,
        )

    def names(self) -> set[str]:
        """All declared live-value names (for the analyzer)."""
        return set(self._entries.keys())

    def active_names(self) -> set[str]:
        """Live-value names whose owning adapter is still active —
        excludes any whose adapter has failed (§120). The interpreter
        uses this to decide which handlers remain eligible."""
        return {
            n for n, e in self._entries.items() if e.status != "inactive"
        }

    def entry(self, name: str) -> LiveValueEntry | None:
        return self._entries.get(name)

    def mark_active(self, name: str) -> None:
        """Called by the interpreter after the first valid value is
        seen for `name` (§117 — `unset` → `active`)."""
        entry = self._entries.get(name)
        if entry is None:
            return
        if entry.status == "unset":
            entry.status = "active"

    def mark_inactive_for_adapter(self, adapter_name: str) -> list[str]:
        """Mark every live value owned by the named adapter as inactive
        (§120). Returns the affected names so the caller can disable
        dependent handlers."""
        affected: list[str] = []
        for entry in self._entries.values():
            if entry.adapter_name == adapter_name and entry.status != "inactive":
                entry.status = "inactive"
                affected.append(entry.name)
        return affected

    def is_unset(self, name: str) -> bool:
        """True if `name` is a declared live value with no value yet —
        conditions involving it evaluate as false per §113."""
        entry = self._entries.get(name)
        return entry is not None and entry.status == "unset"

    def __contains__(self, name: str) -> bool:
        return name in self._entries

    def __len__(self) -> int:
        return len(self._entries)

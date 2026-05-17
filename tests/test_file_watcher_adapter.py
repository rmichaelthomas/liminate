"""Tests for the file-watcher domain pack
(src/liminate/packs/file_watcher.py).

The adapter polls a directory at a configurable interval. Tests use a
short poll interval (20ms) and `tmp_path` so the suite stays fast and
hermetic.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from queue import Empty, Queue

import pytest

from liminate.adapter import AdapterDone, AdapterUpdate, LiveValueDeclaration
from liminate.packs.file_watcher import (
    FileWatcherAdapter,
    FileWatcherDomainPack,
    make_file_watcher_pack,
)


_POLL_MS = 20


def _drain_until_done_or_timeout(q: Queue, *, timeout: float = 1.5) -> list:
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


def _pairs(events: list) -> list[tuple[str, str]]:
    """Reduce events to [(change-type, changed-file), ...] in order.

    Adapter emits `changed-file` first, then `change-type`, so the
    handler reads the right file path at firing time (v3a §119)."""
    updates = [e for e in events if isinstance(e, AdapterUpdate)]
    pairs: list[tuple[str, str]] = []
    i = 0
    while i + 1 < len(updates):
        a, b = updates[i], updates[i + 1]
        if a.name == "changed-file" and b.name == "change-type":
            pairs.append((b.value, a.value))
        i += 2
    return pairs


# ---------------------------------------------------------------------------
# Declarations + construction
# ---------------------------------------------------------------------------


def test_pack_declares_changed_file_and_change_type(tmp_path: Path):
    pack = FileWatcherDomainPack(path=str(tmp_path))
    decls = {d.name: d for d in pack.declarations()}
    assert set(decls) == {"changed-file", "change-type"}
    assert decls["changed-file"] == LiveValueDeclaration(
        name="changed-file", value_type="string",
    )
    assert decls["change-type"] == LiveValueDeclaration(
        name="change-type", value_type="string",
    )


def test_pack_defaults_to_file_watcher_name(tmp_path: Path):
    assert FileWatcherDomainPack(path=str(tmp_path)).name() == "file-watcher"


def test_pack_adapter_is_cached(tmp_path: Path):
    pack = FileWatcherDomainPack(path=str(tmp_path))
    assert pack.adapter() is pack.adapter()


def test_adapter_rejects_nonexistent_path():
    with pytest.raises(ValueError) as exc:
        FileWatcherAdapter(path="/no/such/dir/exists/here")
    assert "does not exist" in str(exc.value)


def test_pack_rejects_nonexistent_path_at_construction():
    """Eager validation — the error should surface at pack construction,
    not at later adapter() time."""
    with pytest.raises(ValueError):
        FileWatcherDomainPack(path="/no/such/dir/exists/here")


def test_adapter_rejects_file_path(tmp_path: Path):
    f = tmp_path / "a-file.txt"
    f.write_text("x")
    with pytest.raises(ValueError) as exc:
        FileWatcherAdapter(path=str(f))
    assert "not a directory" in str(exc.value)


def test_adapter_rejects_non_positive_poll_interval(tmp_path: Path):
    with pytest.raises(ValueError) as exc:
        FileWatcherAdapter(path=str(tmp_path), poll_interval_ms=0)
    assert "poll_interval_ms" in str(exc.value)


def test_adapter_rejects_negative_max_events(tmp_path: Path):
    with pytest.raises(ValueError) as exc:
        FileWatcherAdapter(path=str(tmp_path), max_events=-1)
    assert "max_events" in str(exc.value)


def test_adapter_rejects_recursive(tmp_path: Path):
    with pytest.raises(ValueError) as exc:
        FileWatcherAdapter(path=str(tmp_path), recursive=True)
    assert "recursive" in str(exc.value).lower()


def test_adapter_start_without_queue_raises(tmp_path: Path):
    adapter = FileWatcherAdapter(path=str(tmp_path))
    with pytest.raises(RuntimeError):
        adapter.start()


# ---------------------------------------------------------------------------
# Detection: created / modified / deleted
# ---------------------------------------------------------------------------


def test_adapter_detects_file_creation(tmp_path: Path):
    q: Queue = Queue()
    adapter = FileWatcherAdapter(
        path=str(tmp_path), poll_interval_ms=_POLL_MS, max_events=1,
    )
    adapter.attach_queue(q)
    adapter.start()

    time.sleep(0.05)  # let the initial snapshot complete before creating
    new_file = tmp_path / "fresh.txt"
    new_file.write_text("hi")

    events = _drain_until_done_or_timeout(q)
    adapter.stop()

    pairs = _pairs(events)
    assert pairs, f"no change pairs received; events={events}"
    types = [p[0] for p in pairs]
    paths = [p[1] for p in pairs]
    assert "created" in types
    assert any(os.path.basename(p) == "fresh.txt" for p in paths)


def test_adapter_detects_file_modification(tmp_path: Path):
    target = tmp_path / "tracked.txt"
    target.write_text("v1")

    q: Queue = Queue()
    adapter = FileWatcherAdapter(
        path=str(tmp_path), poll_interval_ms=_POLL_MS, max_events=1,
    )
    adapter.attach_queue(q)
    adapter.start()

    # Sleep briefly so the new mtime is distinguishable from the
    # snapshot taken at start (filesystem mtime resolution varies).
    time.sleep(0.05)
    # Force an mtime change. write_text alone doesn't always bump mtime
    # if it lands in the same fs tick.
    new_mtime = time.time() + 1.0
    target.write_text("v2")
    os.utime(target, (new_mtime, new_mtime))

    events = _drain_until_done_or_timeout(q)
    adapter.stop()

    pairs = _pairs(events)
    assert any(t == "modified" for t, _ in pairs), (
        f"no modification detected; pairs={pairs}"
    )


def test_adapter_detects_file_deletion(tmp_path: Path):
    target = tmp_path / "doomed.txt"
    target.write_text("bye")

    q: Queue = Queue()
    adapter = FileWatcherAdapter(
        path=str(tmp_path), poll_interval_ms=_POLL_MS, max_events=1,
    )
    adapter.attach_queue(q)
    adapter.start()

    target.unlink()

    events = _drain_until_done_or_timeout(q)
    adapter.stop()

    pairs = _pairs(events)
    assert pairs and pairs[0][0] == "deleted"
    assert os.path.basename(pairs[0][1]) == "doomed.txt"


def test_adapter_max_events_bounds_execution(tmp_path: Path):
    """max_events=2 → exactly 2 (type, file) pairs plus AdapterDone."""
    q: Queue = Queue()
    adapter = FileWatcherAdapter(
        path=str(tmp_path), poll_interval_ms=_POLL_MS, max_events=2,
    )
    adapter.attach_queue(q)
    adapter.start()

    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    (tmp_path / "c.txt").write_text("c")  # exceeds the cap

    events = _drain_until_done_or_timeout(q)
    adapter.stop()

    assert any(isinstance(e, AdapterDone) for e in events)
    pairs = _pairs(events)
    assert len(pairs) == 2


def test_adapter_stop_interrupts_idle_poll(tmp_path: Path):
    """stop() must wake a long poll interval promptly. Matches the
    timer pack's interruptibility test."""
    adapter = FileWatcherAdapter(
        path=str(tmp_path), poll_interval_ms=10_000,
    )
    adapter.attach_queue(Queue())
    adapter.start()

    t0 = time.monotonic()
    adapter.stop()
    elapsed = time.monotonic() - t0
    assert elapsed < 1.0, f"stop() took {elapsed:.3f}s — not interruptible"
    assert adapter._thread is not None
    assert not adapter._thread.is_alive()


def test_adapter_stop_is_idempotent(tmp_path: Path):
    adapter = FileWatcherAdapter(path=str(tmp_path), poll_interval_ms=_POLL_MS)
    adapter.attach_queue(Queue())
    adapter.start()
    adapter.stop()
    adapter.stop()


# ---------------------------------------------------------------------------
# Factory + CLI integration
# ---------------------------------------------------------------------------


def test_make_file_watcher_pack_reads_config(tmp_path: Path):
    pack = make_file_watcher_pack({
        "path": str(tmp_path),
        "poll_interval_ms": 75,
        "max_events": 4,
        "name": "inbox",
    })
    assert isinstance(pack, FileWatcherDomainPack)
    assert pack.name() == "inbox"
    adapter = pack.adapter()
    assert adapter.poll_interval_ms == 75
    assert adapter.max_events == 4


def test_make_file_watcher_pack_requires_path():
    with pytest.raises(ValueError) as exc:
        make_file_watcher_pack({})
    assert "path" in str(exc.value)


def test_make_file_watcher_pack_rejects_unknown_keys(tmp_path: Path):
    with pytest.raises(ValueError) as exc:
        make_file_watcher_pack({"path": str(tmp_path), "wat": 1})
    assert "wat" in str(exc.value)


def test_make_file_watcher_pack_rejects_missing_path():
    with pytest.raises(ValueError) as exc:
        make_file_watcher_pack({"path": "/no/such/dir/xyz"})
    assert "does not exist" in str(exc.value)


def test_load_pack_from_arg_inline_file_watcher(tmp_path: Path):
    import json
    from liminate.cli import load_pack_from_arg

    arg = json.dumps({
        "type": "file-watcher",
        "path": str(tmp_path),
        "poll_interval_ms": 50,
        "max_events": 1,
    })
    pack = load_pack_from_arg(arg)
    assert pack.name() == "file-watcher"
    decls = {d.name for d in pack.declarations()}
    assert decls == {"changed-file", "change-type"}

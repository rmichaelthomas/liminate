"""File watcher domain pack — polls a directory for file changes.

Follows the v3a §116–§120 adapter contract: a background thread polls
the watched directory at `poll_interval_ms` and emits one pair of
updates (`change-type`, `changed-file`) for each created, modified,
or deleted file detected between snapshots.

Declarations
------------
- `changed-file` — string; absolute path of the file that changed.
- `change-type`  — string; one of "created", "modified", "deleted".

Notes
-----
- Pure stdlib: `os.scandir` + `stat().st_mtime`. No external
  dependencies (no watchdog).
- Non-recursive by default; recursive watching is deferred.
- The watched directory must exist at adapter construction time; a
  missing path raises `ValueError` immediately rather than failing
  later from the background thread.
- `stop()` is interruptible via `threading.Event.wait(timeout)`,
  matching the timer pack's pattern, so `finish` and external
  shutdown don't block on the poll interval.
- When `max_events` is set, the adapter emits `AdapterDone` after
  reaching the cap. Without it the adapter runs until `stop()`.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

from ..adapter import (
    Adapter,
    AdapterDone,
    AdapterUpdate,
    DomainPack,
    LiveValueDeclaration,
)


_DEFAULT_POLL_INTERVAL_MS = 1000


def _validate_watcher_args(
    path: str | os.PathLike,
    poll_interval_ms: int,
    max_events: int | None,
    recursive: bool,
) -> Path:
    if poll_interval_ms <= 0:
        raise ValueError(
            f"FileWatcherAdapter poll_interval_ms must be positive "
            f"(got {poll_interval_ms})."
        )
    if max_events is not None and max_events < 0:
        raise ValueError(
            f"FileWatcherAdapter max_events must be >= 0 or None "
            f"(got {max_events})."
        )
    if recursive:
        # Deferred — see module docstring.
        raise ValueError(
            "FileWatcherAdapter recursive=True is not yet supported; "
            "recursive watching is deferred."
        )
    p = Path(path)
    if not p.exists():
        raise ValueError(
            f"FileWatcherAdapter path does not exist: {path!r}."
        )
    if not p.is_dir():
        raise ValueError(
            f"FileWatcherAdapter path is not a directory: {path!r}."
        )
    return p


def _snapshot(directory: Path) -> dict[str, float]:
    """Return {absolute_path: mtime} for files (non-recursive) in `directory`.

    Files that disappear between scandir and stat are skipped silently —
    they'd otherwise show up in the next poll as deletions anyway."""
    result: dict[str, float] = {}
    try:
        with os.scandir(directory) as it:
            for entry in it:
                if not entry.is_file(follow_symlinks=False):
                    continue
                try:
                    mtime = entry.stat(follow_symlinks=False).st_mtime
                except (FileNotFoundError, PermissionError):
                    continue
                result[os.path.abspath(entry.path)] = mtime
    except (FileNotFoundError, PermissionError):
        # Directory removed or unreadable mid-poll — treat as empty;
        # subsequent polls will surface deletions naturally.
        return {}
    return result


class FileWatcherAdapter(Adapter):
    """Polls a directory; pushes (change-type, changed-file) update pairs."""

    def __init__(
        self,
        *,
        path: str | os.PathLike,
        poll_interval_ms: int = _DEFAULT_POLL_INTERVAL_MS,
        max_events: int | None = None,
        recursive: bool = False,
        name: str = "file-watcher",
    ) -> None:
        super().__init__(name=name)
        self._path = _validate_watcher_args(
            path, poll_interval_ms, max_events, recursive,
        )
        self.poll_interval_ms = poll_interval_ms
        self.max_events = max_events
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self.queue is None:
            raise RuntimeError(
                "FileWatcherAdapter.start() called before attach_queue()."
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
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)

    def _emit(self, change_type: str, file_path: str) -> bool:
        """Push one (changed-file, change-type) update pair. Returns
        True if the caller should keep going, False if `max_events`
        has been reached and `AdapterDone` was emitted.

        `changed-file` is emitted first so a `when change-type is
        equal to "created"` handler sees the correct `changed-file`
        value when it fires (v3a §119: one update processed at a time;
        the handler reads symbol state at firing time)."""
        self.queue.put(AdapterUpdate(name="changed-file", value=file_path))
        self.queue.put(AdapterUpdate(name="change-type", value=change_type))
        self._events_emitted += 1
        if (
            self.max_events is not None
            and self._events_emitted >= self.max_events
        ):
            self.queue.put(AdapterDone(adapter_name=self.name))
            return False
        return True

    def _run(self) -> None:
        interval_s = self.poll_interval_ms / 1000.0
        self._events_emitted = 0
        previous = _snapshot(self._path)

        while not self._stop_event.is_set():
            if self._stop_event.wait(timeout=interval_s):
                return
            current = _snapshot(self._path)

            # Created: in current, not in previous.
            for path, _ in current.items():
                if path not in previous:
                    if not self._emit("created", path):
                        return
            # Modified: in both, mtime changed.
            for path, mtime in current.items():
                if path in previous and previous[path] != mtime:
                    if not self._emit("modified", path):
                        return
            # Deleted: in previous, not in current.
            for path in previous:
                if path not in current:
                    if not self._emit("deleted", path):
                        return

            previous = current


class FileWatcherDomainPack(DomainPack):
    """DomainPack wrapping a FileWatcherAdapter."""

    def __init__(
        self,
        *,
        path: str | os.PathLike,
        poll_interval_ms: int = _DEFAULT_POLL_INTERVAL_MS,
        max_events: int | None = None,
        recursive: bool = False,
        name: str = "file-watcher",
    ) -> None:
        # Validate eagerly so construction-time errors surface at the
        # CLI rather than later from the background thread.
        _validate_watcher_args(path, poll_interval_ms, max_events, recursive)
        self._name = name
        self._path = path
        self._poll_interval_ms = poll_interval_ms
        self._max_events = max_events
        self._recursive = recursive
        self._adapter: FileWatcherAdapter | None = None

    def name(self) -> str:
        return self._name

    def declarations(self) -> list[LiveValueDeclaration]:
        return [
            LiveValueDeclaration(name="changed-file", value_type="string"),
            LiveValueDeclaration(name="change-type", value_type="string"),
        ]

    def adapter(self) -> Adapter:
        if self._adapter is None:
            self._adapter = FileWatcherAdapter(
                path=self._path,
                poll_interval_ms=self._poll_interval_ms,
                max_events=self._max_events,
                recursive=self._recursive,
                name=self._name,
            )
        return self._adapter


_WATCHER_CONFIG_KEYS = {
    "path", "poll_interval_ms", "max_events", "recursive", "name",
}


def make_file_watcher_pack(config: dict[str, Any]) -> FileWatcherDomainPack:
    """Factory used by the CLI `--pack` flag when `type == "file-watcher"`.

    Required keys:
      - `path`: directory to watch.
    Optional keys:
      - `poll_interval_ms`: int, default 1000.
      - `max_events`:       int or null, default null (run forever).
      - `recursive`:        bool, default false (recursive deferred).
      - `name`:             str, default "file-watcher".
    Unknown keys raise."""
    extra = set(config) - _WATCHER_CONFIG_KEYS - {"type"}
    if extra:
        raise ValueError(
            f"file-watcher pack config has unknown key(s): {sorted(extra)}. "
            f"Allowed: {sorted(_WATCHER_CONFIG_KEYS)}."
        )
    if "path" not in config:
        raise ValueError(
            "file-watcher pack config requires a 'path' key (directory to watch)."
        )
    return FileWatcherDomainPack(
        path=str(config["path"]),
        poll_interval_ms=int(
            config.get("poll_interval_ms", _DEFAULT_POLL_INTERVAL_MS)
        ),
        max_events=(
            int(config["max_events"])
            if config.get("max_events") is not None
            else None
        ),
        recursive=bool(config.get("recursive", False)),
        name=str(config.get("name", "file-watcher")),
    )

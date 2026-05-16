"""Tests for the stdin domain pack (src/liminate/packs/stdin.py).

The stdin pack reads lines from `sys.stdin` (or an injected stream)
on a daemon background thread. Tests inject an in-memory
`io.StringIO` so the suite remains deterministic and fast.
"""

from __future__ import annotations

import io
import time
from queue import Empty, Queue

import pytest

from liminate.adapter import AdapterDone, AdapterUpdate, LiveValueDeclaration
from liminate.packs.stdin import (
    StdinAdapter,
    StdinDomainPack,
    make_stdin_pack,
)


def _drain_until_done(q: Queue, *, timeout: float = 2.0) -> list:
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


# ---------------------------------------------------------------------------
# Declarations
# ---------------------------------------------------------------------------


def test_stdin_pack_declares_line_as_string():
    pack = StdinDomainPack()
    decls = pack.declarations()
    assert decls == [LiveValueDeclaration(name="line", value_type="string")]


def test_stdin_pack_name_defaults_to_stdin():
    assert StdinDomainPack().name() == "stdin"


def test_stdin_pack_adapter_is_cached():
    pack = StdinDomainPack()
    assert pack.adapter() is pack.adapter()


# ---------------------------------------------------------------------------
# Adapter behavior
# ---------------------------------------------------------------------------


def test_stdin_adapter_emits_each_line_and_then_done():
    q: Queue = Queue()
    stream = io.StringIO("hello\nworld\n")
    adapter = StdinAdapter(stream=stream)
    adapter.attach_queue(q)
    adapter.start()
    events = _drain_until_done(q)
    adapter.stop()

    updates = [e for e in events if isinstance(e, AdapterUpdate)]
    assert [(u.name, u.value) for u in updates] == [
        ("line", "hello"),
        ("line", "world"),
    ]
    done = [e for e in events if isinstance(e, AdapterDone)]
    assert len(done) == 1
    assert done[0].adapter_name == "stdin"
    assert events[-1] is done[0]


def test_stdin_adapter_pushes_empty_and_whitespace_lines():
    """Empty/whitespace lines are valid data — only true EOF signals done."""
    q: Queue = Queue()
    stream = io.StringIO("\n   \nx\n")
    adapter = StdinAdapter(stream=stream)
    adapter.attach_queue(q)
    adapter.start()
    events = _drain_until_done(q)
    adapter.stop()

    updates = [e for e in events if isinstance(e, AdapterUpdate)]
    assert [u.value for u in updates] == ["", "   ", "x"]


def test_stdin_adapter_eof_without_trailing_newline_still_emits_line():
    q: Queue = Queue()
    stream = io.StringIO("last")  # no trailing newline
    adapter = StdinAdapter(stream=stream)
    adapter.attach_queue(q)
    adapter.start()
    events = _drain_until_done(q)
    adapter.stop()

    updates = [e for e in events if isinstance(e, AdapterUpdate)]
    assert [u.value for u in updates] == ["last"]
    assert any(isinstance(e, AdapterDone) for e in events)


def test_stdin_adapter_immediate_eof_emits_only_done():
    q: Queue = Queue()
    adapter = StdinAdapter(stream=io.StringIO(""))
    adapter.attach_queue(q)
    adapter.start()
    events = _drain_until_done(q)
    adapter.stop()

    assert [type(e) for e in events] == [AdapterDone]


def test_stdin_adapter_start_without_queue_raises():
    adapter = StdinAdapter(stream=io.StringIO(""))
    with pytest.raises(RuntimeError):
        adapter.start()


def test_stdin_adapter_stop_is_idempotent():
    adapter = StdinAdapter(stream=io.StringIO(""))
    adapter.attach_queue(Queue())
    adapter.start()
    adapter.stop()
    adapter.stop()  # second call must not raise


def test_stdin_adapter_strips_crlf():
    q: Queue = Queue()
    stream = io.StringIO("hello\r\nworld\r\n")
    adapter = StdinAdapter(stream=stream)
    adapter.attach_queue(q)
    adapter.start()
    events = _drain_until_done(q)
    adapter.stop()

    updates = [e for e in events if isinstance(e, AdapterUpdate)]
    assert [u.value for u in updates] == ["hello", "world"]


# ---------------------------------------------------------------------------
# Factory + CLI integration
# ---------------------------------------------------------------------------


def test_make_stdin_pack_defaults():
    pack = make_stdin_pack({})
    assert isinstance(pack, StdinDomainPack)
    assert pack.name() == "stdin"


def test_make_stdin_pack_accepts_custom_name():
    pack = make_stdin_pack({"name": "input-stream"})
    assert pack.name() == "input-stream"


def test_make_stdin_pack_rejects_unknown_keys():
    with pytest.raises(ValueError) as exc:
        make_stdin_pack({"path": "/tmp"})  # path belongs to file-watcher
    assert "path" in str(exc.value)


def test_load_pack_from_arg_inline_stdin():
    from liminate.cli import load_pack_from_arg

    pack = load_pack_from_arg('{"type": "stdin"}')
    assert pack.name() == "stdin"
    decls = {d.name for d in pack.declarations()}
    assert decls == {"line"}

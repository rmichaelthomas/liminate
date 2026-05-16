"""Phase 7 gate tests: adapter infrastructure (v3a §116/§117/§118/§119/§120)."""

import pytest

from queue import Queue

from liminate.adapter import (
    Adapter,
    AdapterDone,
    AdapterFailure,
    AdapterUpdate,
    DomainPack,
    LiveValueDeclaration,
    LiveValueRegistry,
    TestAdapter,
    TestDomainPack,
)


# ---------------------------------------------------------------------------
# LiveValueDeclaration / queue message shapes
# ---------------------------------------------------------------------------


def test_live_value_declaration_is_immutable():
    """v3a §116: declarations are intended to be set-once per pack
    construction; frozen=True catches accidental mutation."""
    d = LiveValueDeclaration(name="temperature", value_type="number")
    with pytest.raises(Exception):  # FrozenInstanceError
        d.name = "humidity"  # type: ignore[misc]


def test_adapter_update_carries_name_and_value():
    u = AdapterUpdate(name="temperature", value=105)
    assert u.name == "temperature"
    assert u.value == 105


def test_adapter_done_carries_adapter_name():
    d = AdapterDone(adapter_name="test-pack")
    assert d.adapter_name == "test-pack"


def test_adapter_failure_carries_name_and_reason():
    f = AdapterFailure(adapter_name="bad-pack", reason="boom")
    assert f.adapter_name == "bad-pack"
    assert f.reason == "boom"


# ---------------------------------------------------------------------------
# TestAdapter
# ---------------------------------------------------------------------------


def _drain(q: Queue) -> list:
    out = []
    while not q.empty():
        out.append(q.get_nowait())
    return out


def test_test_adapter_enqueues_scripted_updates_in_order():
    q: Queue = Queue()
    adapter = TestAdapter([
        ("temperature", 100),
        ("humidity", 50),
        ("temperature", 110),
    ], name="test")
    adapter.attach_queue(q)
    adapter.start()

    events = _drain(q)
    # Updates in order + auto-appended Done.
    assert isinstance(events[0], AdapterUpdate) and events[0].name == "temperature" and events[0].value == 100
    assert isinstance(events[1], AdapterUpdate) and events[1].name == "humidity" and events[1].value == 50
    assert isinstance(events[2], AdapterUpdate) and events[2].name == "temperature" and events[2].value == 110
    assert isinstance(events[3], AdapterDone) and events[3].adapter_name == "test"


def test_test_adapter_explicit_done_is_honored():
    """When the script already ends with `[done]`, the adapter does
    not append a second AdapterDone."""
    q: Queue = Queue()
    adapter = TestAdapter([("temperature", 100), "[done]"], name="test")
    adapter.attach_queue(q)
    adapter.start()

    events = _drain(q)
    assert len(events) == 2
    assert isinstance(events[0], AdapterUpdate)
    assert isinstance(events[1], AdapterDone)


def test_test_adapter_start_without_queue_raises():
    """Defensive: start() before attach_queue() is a programmer error."""
    adapter = TestAdapter([("x", 1)])
    with pytest.raises(RuntimeError):
        adapter.start()


def test_test_adapter_start_is_idempotent():
    q: Queue = Queue()
    adapter = TestAdapter([("temperature", 100)])
    adapter.attach_queue(q)
    adapter.start()
    first = _drain(q)
    adapter.start()  # second call should be a no-op
    second = _drain(q)
    assert len(first) == 2  # update + auto-done
    assert second == []


def test_test_adapter_malformed_script_yields_failure():
    """v3a §120 — malformed script entries are surfaced as
    AdapterFailure so the interpreter can isolate the bad adapter."""
    q: Queue = Queue()
    adapter = TestAdapter([("temperature", 100), 42, ("humidity", 50)], name="bad")
    adapter.attach_queue(q)
    adapter.start()
    events = _drain(q)
    assert len(events) == 2
    assert isinstance(events[0], AdapterUpdate)
    assert isinstance(events[1], AdapterFailure)
    assert events[1].adapter_name == "bad"


def test_test_adapter_stop_marks_stopped():
    adapter = TestAdapter([])
    assert adapter.stopped is False
    adapter.stop()
    assert adapter.stopped is True
    adapter.stop()  # idempotent
    assert adapter.stopped is True


# ---------------------------------------------------------------------------
# TestDomainPack
# ---------------------------------------------------------------------------


def test_test_domain_pack_yields_declarations_and_adapter():
    pack = TestDomainPack(
        declarations=[("temperature", "number"), ("humidity", "number")],
        script=[("temperature", 100)],
        name="weather",
    )
    assert pack.name() == "weather"
    decls = pack.declarations()
    assert len(decls) == 2
    assert decls[0] == LiveValueDeclaration(name="temperature", value_type="number")

    adapter = pack.adapter()
    assert isinstance(adapter, TestAdapter)
    # Repeated adapter() returns the same instance (single adapter per pack).
    assert pack.adapter() is adapter


def test_test_domain_pack_accepts_declaration_objects():
    decls = [
        LiveValueDeclaration(name="patient", value_type="record"),
    ]
    pack = TestDomainPack(declarations=decls, script=[])
    assert pack.declarations()[0].name == "patient"


# ---------------------------------------------------------------------------
# LiveValueRegistry (§117 lifecycle)
# ---------------------------------------------------------------------------


def test_registry_declare_creates_unset_entries():
    reg = LiveValueRegistry()
    reg.declare(LiveValueDeclaration("temperature", "number"), "pack-a")
    entry = reg.entry("temperature")
    assert entry is not None
    assert entry.status == "unset"
    assert entry.value_type == "number"
    assert entry.adapter_name == "pack-a"


def test_registry_rejects_duplicate_declarations():
    """v3a §116: two adapters providing the same live value name is a
    startup error."""
    reg = LiveValueRegistry()
    reg.declare(LiveValueDeclaration("temperature", "number"), "pack-a")
    with pytest.raises(ValueError) as exc:
        reg.declare(LiveValueDeclaration("temperature", "number"), "pack-b")
    assert "already declared" in str(exc.value)


def test_registry_names_returns_all_declared():
    reg = LiveValueRegistry()
    reg.declare(LiveValueDeclaration("temperature", "number"), "pack-a")
    reg.declare(LiveValueDeclaration("humidity", "number"), "pack-a")
    assert reg.names() == {"temperature", "humidity"}


def test_registry_mark_active_transitions_unset_to_active():
    reg = LiveValueRegistry()
    reg.declare(LiveValueDeclaration("temperature", "number"), "pack-a")
    assert reg.is_unset("temperature") is True

    reg.mark_active("temperature")
    assert reg.is_unset("temperature") is False
    entry = reg.entry("temperature")
    assert entry.status == "active"


def test_registry_mark_active_is_idempotent_after_first():
    reg = LiveValueRegistry()
    reg.declare(LiveValueDeclaration("temperature", "number"), "pack-a")
    reg.mark_active("temperature")
    reg.mark_active("temperature")  # idempotent
    entry = reg.entry("temperature")
    assert entry.status == "active"


def test_registry_mark_inactive_for_adapter_returns_affected_names():
    """v3a §120: when an adapter fails, all its live values transition
    to inactive. The registry returns the affected names so the caller
    can disable dependent handlers."""
    reg = LiveValueRegistry()
    reg.declare(LiveValueDeclaration("temperature", "number"), "pack-a")
    reg.declare(LiveValueDeclaration("humidity", "number"), "pack-a")
    reg.declare(LiveValueDeclaration("patient", "record"), "pack-b")

    affected = reg.mark_inactive_for_adapter("pack-a")
    assert set(affected) == {"temperature", "humidity"}
    assert reg.entry("temperature").status == "inactive"
    assert reg.entry("humidity").status == "inactive"
    # Other adapter unaffected.
    assert reg.entry("patient").status == "unset"


def test_registry_active_names_excludes_inactive():
    reg = LiveValueRegistry()
    reg.declare(LiveValueDeclaration("temperature", "number"), "pack-a")
    reg.declare(LiveValueDeclaration("patient", "record"), "pack-b")
    reg.mark_inactive_for_adapter("pack-a")
    assert reg.active_names() == {"patient"}


def test_registry_contains_and_len():
    reg = LiveValueRegistry()
    assert "temperature" not in reg
    assert len(reg) == 0
    reg.declare(LiveValueDeclaration("temperature", "number"), "pack-a")
    assert "temperature" in reg
    assert len(reg) == 1


# ---------------------------------------------------------------------------
# Adapter/DomainPack as ABCs (informal protocol check)
# ---------------------------------------------------------------------------


def test_adapter_is_abstract():
    """Adapter and DomainPack are ABCs — instantiating directly is a
    programmer error. Concrete subclasses must implement start/stop /
    declarations/adapter."""
    with pytest.raises(TypeError):
        Adapter()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        DomainPack()  # type: ignore[abstract]

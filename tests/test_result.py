"""Phase 1 gate tests: structured result objects
(v1c §50, v1d §64, v3a §122)."""

from liminate.result import LiminateResult, ResultStatus


def test_all_ten_statuses_present():
    # v3a §122: the five-outcome taxonomy is extended by four
    # listener-mode statuses (LISTENING, HANDLER_FIRE, SHUTDOWN,
    # ERROR_RUNTIME) for Phase 2 execution. Normative Era batch 2
    # adds REQUIREMENT_NOT_MET — distinct from ERROR_SEMANTIC ("the
    # program has a bug"); REQUIREMENT_NOT_MET means "the data
    # violates a rule" enforced by a `require` statement. Deontic Era
    # adds PROHIBITION_VIOLATED — the `forbid` counterpart, raised when
    # a prohibited condition evaluates true.
    names = {s.name for s in ResultStatus}
    assert names == {
        "SUCCESS", "AMBER_PRECEDENCE", "AMBER_AMBIGUITY",
        "ERROR_PARSE", "ERROR_SEMANTIC",
        "LISTENING", "HANDLER_FIRE", "SHUTDOWN", "ERROR_RUNTIME",
        "REQUIREMENT_NOT_MET", "PROHIBITION_VIOLATED",
    }


def test_construct_success_with_output():
    r = LiminateResult(
        status=ResultStatus.SUCCESS,
        canonical="show age",
        output=["30"],
        executed=True,
    )
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["30"]
    assert r.executed is True
    assert r.message is None


def test_construct_amber_precedence():
    r = LiminateResult(
        status=ResultStatus.AMBER_PRECEDENCE,
        canonical="filter the orders where (a and b) or c",
        message="I'll read this as: (A AND B) OR C. Is that what you mean?",
        executed=False,
    )
    assert r.status is ResultStatus.AMBER_PRECEDENCE
    assert r.executed is False
    assert r.message is not None


def test_construct_amber_ambiguity():
    r = LiminateResult(
        status=ResultStatus.AMBER_AMBIGUITY,
        message="I'm not sure if you mean X or Y — can you clarify?",
    )
    assert r.status is ResultStatus.AMBER_AMBIGUITY
    assert r.executed is False


def test_construct_error_parse():
    r = LiminateResult(
        status=ResultStatus.ERROR_PARSE,
        message="I don't recognize a command here.",
    )
    assert r.status is ResultStatus.ERROR_PARSE
    assert r.canonical is None
    assert r.executed is False


def test_construct_error_semantic():
    r = LiminateResult(
        status=ResultStatus.ERROR_SEMANTIC,
        canonical="show missingname",
        message="I can't find 'missingname'.",
    )
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert r.canonical == "show missingname"
    assert r.executed is False


def test_default_fields():
    r = LiminateResult(status=ResultStatus.SUCCESS)
    assert r.canonical is None
    assert r.output is None
    assert r.message is None
    assert r.executed is False
    assert r.pending_ast is None
    # v3a §122: metadata defaults to None — Phase 1 results carry the
    # v2d-identical shape (no metadata) without any code change.
    assert r.metadata is None


# ---------- v3a §122: listener-mode statuses + metadata ----------


def test_construct_listening_marker():
    """LISTENING is yielded once when Phase 2 begins. `watching` lists
    every name referenced by any registered handler (v3a §108 dependency
    extraction + §122 marker shape)."""
    r = LiminateResult(
        status=ResultStatus.LISTENING,
        metadata={"watching": ["temperature", "humidity"]},
    )
    assert r.status is ResultStatus.LISTENING
    assert r.metadata["watching"] == ["temperature", "humidity"]


def test_construct_handler_fire_with_trigger_metadata():
    """HANDLER_FIRE wraps each action-block statement result with
    trigger metadata identifying source, handler index, and what
    changed (v3a §122 trigger envelope)."""
    r = LiminateResult(
        status=ResultStatus.HANDLER_FIRE,
        canonical='show "alert"',
        output=["alert"],
        executed=True,
        metadata={
            "trigger": {
                "source": "adapter_update",
                "handler_index": 0,
                "values_changed": ["temperature"],
                "new_values": {"temperature": 105},
            }
        },
    )
    assert r.status is ResultStatus.HANDLER_FIRE
    assert r.metadata["trigger"]["source"] == "adapter_update"
    assert r.metadata["trigger"]["values_changed"] == ["temperature"]
    assert r.metadata["trigger"]["new_values"]["temperature"] == 105


def test_construct_shutdown_with_reason():
    """SHUTDOWN carries a `reason` identifying why the listener stopped
    (v3a §122 — one of: finish, adapter_complete, external, no_adapters,
    error)."""
    r = LiminateResult(
        status=ResultStatus.SHUTDOWN,
        output=["Program stopped."],
        metadata={"reason": "finish", "handler_index": 2},
    )
    assert r.status is ResultStatus.SHUTDOWN
    assert r.metadata["reason"] == "finish"
    assert r.metadata["handler_index"] == 2


def test_construct_error_runtime():
    """ERROR_RUNTIME covers listener-specific failures: cycle detection
    (v3a §114), adapter failure (v3a §120), type mismatch (v3a §116)."""
    r = LiminateResult(
        status=ResultStatus.ERROR_RUNTIME,
        message="A handler fired twice in one cascade — cycle detected.",
        metadata={"kind": "cycle", "path": ["h0", "h1", "h0"]},
    )
    assert r.status is ResultStatus.ERROR_RUNTIME
    assert r.metadata["kind"] == "cycle"


def test_metadata_is_independent_per_instance():
    """Each LiminateResult must own its metadata dict — the default
    mustn't be a shared mutable. Defensive against the common dataclass
    default-mutable-arg footgun."""
    a = LiminateResult(status=ResultStatus.SUCCESS)
    b = LiminateResult(status=ResultStatus.SUCCESS)
    assert a.metadata is None
    assert b.metadata is None
    # Setting one must not affect the other.
    a.metadata = {"watching": ["x"]}
    assert b.metadata is None

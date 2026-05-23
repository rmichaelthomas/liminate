"""Tests for the --verbose CLI flag (v5 §17)."""
from __future__ import annotations

import io
import json

from liminate.cli import run_file


def test_verbose_emits_metadata_to_stderr(tmp_path):
    src = tmp_path / "test.limn"
    src.write_text('remember a string called x with "hello"\nshow x\n')

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    run_file(
        str(src),
        verbose=True,
        quiet=True,
        out=stdout_capture,
        verbose_out=stderr_capture,
    )

    metadata = [json.loads(line) for line in stderr_capture.getvalue().splitlines()]
    assert [m["line"] for m in metadata] == [1, 2]
    for item in metadata:
        assert item["timestamp"].endswith("Z") or "+" in item["timestamp"]
        assert isinstance(item["duration_ms"], (int, float))
        assert item["duration_ms"] >= 0


def test_verbose_off_emits_no_metadata(tmp_path):
    src = tmp_path / "test.limn"
    src.write_text('remember a string called x with "hello"\n')

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    run_file(
        str(src),
        verbose=False,
        quiet=True,
        out=stdout_capture,
        verbose_out=stderr_capture,
    )

    assert stderr_capture.getvalue() == ""
    for line in stdout_capture.getvalue().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            json.loads(line)
            assert False, f"Unexpected JSON in non-verbose output: {line}"
        except json.JSONDecodeError:
            pass


def test_quiet_verbose_combination(tmp_path):
    src = tmp_path / "test.limn"
    src.write_text('remember a string called x with "hello"\n')

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    run_file(
        str(src),
        verbose=True,
        quiet=True,
        out=stdout_capture,
        verbose_out=stderr_capture,
    )

    assert "I understand this as:" not in stdout_capture.getvalue()
    metadata = [json.loads(line) for line in stderr_capture.getvalue().splitlines()]
    assert len(metadata) == 1
    assert metadata[0]["line"] == 1

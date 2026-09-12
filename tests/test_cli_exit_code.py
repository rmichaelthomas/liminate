"""Tests for CLI exit code propagation (audit finding #1)."""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

LIMINATE = [sys.executable, "-m", "liminate"]


def _run(source: str, *, pack: str | None = None) -> subprocess.CompletedProcess:
    tmp = Path("/tmp/test_exit_code.limn")
    tmp.write_text(source, encoding="utf-8")
    cmd = list(LIMINATE)
    if pack:
        cmd += ["--pack", pack]
    cmd.append(str(tmp))
    return subprocess.run(cmd, capture_output=True, text=True)


class TestExitCode:
    def test_valid_contract_exits_zero(self):
        result = _run('remember a string called x with "hello"\nshow x')
        assert result.returncode == 0

    def test_parse_error_exits_nonzero(self):
        result = _run('invoke "hello"')
        assert result.returncode == 1

    def test_semantic_error_exits_nonzero(self):
        result = _run('add "item" to nonexistent-list')
        assert result.returncode == 1

    def test_error_after_valid_lines_still_exits_nonzero(self):
        source = textwrap.dedent("""\
            remember a string called x with "hello"
            show x
            invoke "broken"
        """)
        result = _run(source)
        assert result.returncode == 1

    def test_violated_prohibition_exits_nonzero(self):
        """A `forbid` that fires is the deontic core saying no. It exited 0,
        which made it less consequential to a shell than a pack verb: a failed
        `cite` already exits 1. Every shell consumer was string-matching
        "Prohibition violated" to find out, and one that forgot reported a
        denial as an admission."""
        source = textwrap.dedent("""\
            remember a value called anchor with "no"
            forbid anchor is "no" because "a lifted manifest binds to no file"
        """)
        result = _run(source)
        assert result.returncode == 1

    def test_unmet_requirement_exits_nonzero(self):
        """`require` is the same verb from the other side and had the same
        silence."""
        source = textwrap.dedent("""\
            remember a date called starts-at with 2025-03-15
            require starts-at is not below 2026-01-01
        """)
        result = _run(source)
        assert result.returncode == 1

    def test_a_satisfied_deontic_statement_still_exits_zero(self):
        """The exit code says a rule fired, not that rules exist."""
        source = textwrap.dedent("""\
            remember a value called anchor with "yes"
            forbid anchor is "no" because "a lifted manifest binds to no file"
            require anchor is "yes"
        """)
        result = _run(source)
        assert result.returncode == 0

    def test_help_exits_zero(self):
        result = subprocess.run(
            LIMINATE + ["--help"], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_short_help_exits_zero(self):
        result = subprocess.run(
            LIMINATE + ["-h"], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_version_exits_zero(self):
        result = subprocess.run(
            LIMINATE + ["--version"], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Liminate" in result.stdout

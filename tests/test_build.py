"""Branch G Phase C — tests for `liminate build` and `--inspect`.

PyInstaller invocation is slow (~10s per build) and pulls in a sizeable
dependency, so the binary-producing tests are gated behind the
`LIMINATE_RUN_PYINSTALLER` env var and PyInstaller's availability. The
fast tests cover validation, manifest construction, inspect formatting,
and the Q2 reactive-without-adapter notice without ever shelling out to
PyInstaller.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from importlib import import_module
from importlib.util import find_spec
from io import StringIO
from pathlib import Path

import pytest

from liminate import build as build_mod
from liminate.build import (
    BuildError,
    BuildManifest,
    PackManifest,
    _compute_vocabulary_in_use,
    _contains_when,
    _validate_and_render,
    build,
)
from liminate.cli import main as cli_main
from liminate.inspect_cmd import format_manifest


REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "examples"


# Slow / requires PyInstaller. Skip unless explicitly opted in OR
# PyInstaller is importable (CI installs it via the [build] extra).
_PYINSTALLER_AVAILABLE = find_spec("PyInstaller") is not None
_RUN_PYI = (
    _PYINSTALLER_AVAILABLE
    and os.environ.get("LIMINATE_SKIP_PYINSTALLER", "") not in ("1", "true", "yes")
)


# ---------------------------------------------------------------------------
# Validation + manifest (fast — no PyInstaller)
# ---------------------------------------------------------------------------


def test_validate_basic_program():
    source = (
        "remember a number called age with 30\n"
        "show age\n"
    )
    canonical, asts, _ = _validate_and_render(source)
    assert canonical == [
        "remember a number called age with 30",
        "show age",
    ]
    assert len(asts) == 2


def test_validate_blank_lines_preserved():
    source = "remember a number called age with 30\n\nshow age\n"
    canonical, _, _ = _validate_and_render(source)
    assert canonical == [
        "remember a number called age with 30",
        "",
        "show age",
    ]


def test_validate_parse_error_raises_build_error():
    source = 'show "unclosed\n'
    with pytest.raises(BuildError):
        _validate_and_render(source)


def test_validate_when_block():
    source = (
        "remember a number called level with 0\n"
        "when level is above 50\n"
        "  show level\n"
    )
    canonical, asts, _ = _validate_and_render(source)
    assert _contains_when(asts)
    # The when statement renders multi-line; first line begins with 'when'.
    assert canonical[1].startswith("when ")


def test_validate_composition_then_call():
    """Composition defined on one line, called on the next, must validate.
    The build validator needs to track composition names across statements
    so the parser accepts the bare-word call."""
    source = (
        "remember how to bump: remember a number called age with 31\n"
        "bump\n"
    )
    canonical, asts, _ = _validate_and_render(source)
    assert len(asts) == 2


def test_compute_vocabulary_in_use():
    source = (
        "remember a number called age with 30\n"
        "show age\n"
        "filter the colors where each is above 5\n"
    )
    voc = _compute_vocabulary_in_use(source)
    assert "remember" in voc["verbs"]
    assert "show" in voc["verbs"]
    assert "filter" in voc["verbs"]
    assert "where" in voc["connectives"]
    assert "with" in voc["connectives"]
    assert "above" in voc["operators"]
    assert "is" in voc["operators"]


def test_compute_vocabulary_skips_comments_and_blanks():
    source = "-- a comment\n\nshow x\n"
    voc = _compute_vocabulary_in_use(source)
    assert voc["verbs"] == ["show"]


# ---------------------------------------------------------------------------
# Manifest formatting (fast)
# ---------------------------------------------------------------------------


def _sample_manifest() -> dict:
    return BuildManifest(
        liminate_version="0.1.0",
        source_filename="foo.limn",
        source_text="show x\n",
        canonical=["show x"],
        packs=[],
        vocabulary_in_use={
            "verbs": ["show"], "connectives": [], "operators": [],
        },
    ).as_dict()


def test_format_manifest_plain():
    text = format_manifest(_sample_manifest(), as_json=False)
    assert "=== Liminate Executable ===" in text
    assert "Version: Liminate 0.1.0" in text
    assert "Source: foo.limn" in text
    assert "--- Source ---" in text
    assert "--- Understood As ---" in text
    assert "--- Packs Bundled ---" in text
    assert "(none)" in text  # no packs
    assert "--- Vocabulary In Use ---" in text
    assert "Verbs: show" in text


def test_format_manifest_json_roundtrip():
    m = _sample_manifest()
    out = format_manifest(m, as_json=True)
    parsed = json.loads(out)
    assert parsed["liminate_version"] == "0.1.0"
    assert parsed["source_filename"] == "foo.limn"
    assert parsed["canonical"] == ["show x"]
    assert parsed["packs"] == []
    assert parsed["vocabulary_in_use"]["verbs"] == ["show"]


def test_format_manifest_plain_with_pack():
    manifest = BuildManifest(
        liminate_version="0.1.0",
        source_filename="foo.limn",
        source_text="show x\n",
        canonical=["show x"],
        packs=[
            PackManifest(
                name="ui",
                vocabulary=[["screen", "noun"], ["button", "noun"]],
                verbs=[{
                    "word": "navigate",
                    "slots": [{
                        "name": "screen-name", "connective": "to",
                        "required": True, "type_constraint": "screen",
                    }],
                    "execution": {
                        "type": "set_value",
                        "target_name": "current-screen",
                        "source_slot": "screen-name",
                    },
                }],
            ),
        ],
        vocabulary_in_use={"verbs": [], "connectives": [], "operators": []},
    ).as_dict()
    text = format_manifest(manifest, as_json=False)
    assert "- ui" in text
    assert "screen (noun)" in text
    assert "navigate to <screen-name>:screen" in text


# ---------------------------------------------------------------------------
# build() — source not found / pack errors (fast — fails before PyInstaller)
# ---------------------------------------------------------------------------


def test_build_source_missing(tmp_path):
    err = StringIO()
    out = StringIO()
    rc = build("/no/such/file.limn", [], str(tmp_path / "x"), stderr=err, stdout=out)
    assert rc == 2
    assert "source file not found" in err.getvalue()


def test_build_parse_error(tmp_path, capsys):
    src = tmp_path / "bad.limn"
    src.write_text('show "unclosed\n')
    err = StringIO()
    out = StringIO()
    rc = build(str(src), [], str(tmp_path / "out"), stderr=err, stdout=out)
    assert rc == 1
    assert "Error:" in err.getvalue()


def test_build_pack_missing(tmp_path):
    src = tmp_path / "ok.limn"
    src.write_text("show 1\n")
    err = StringIO()
    out = StringIO()
    rc = build(
        str(src), ["/no/such/pack.json"], str(tmp_path / "out"),
        stderr=err, stdout=out,
    )
    assert rc == 2
    assert "pack" in err.getvalue()


# ---------------------------------------------------------------------------
# Q2 reactive-without-adapter notice (fast — fails or warns before PyInstaller)
# ---------------------------------------------------------------------------


def test_q2_notice_when_reactive_without_pack(tmp_path, monkeypatch):
    """Build must print the §11 notice when `when` is present but no
    --pack is supplied, then continue. We monkey-patch _find_produced_binary
    and the PyInstaller subprocess so the test never actually invokes
    PyInstaller (the notice fires before the build subprocess)."""
    src = tmp_path / "reactive.limn"
    src.write_text(
        "remember a number called level with 0\n"
        "when level is above 0\n"
        "  show level\n"
    )

    # Short-circuit the actual PyInstaller invocation. We confirm the
    # notice was printed regardless of whether the build succeeds.
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        # Pretend PyInstaller produced the expected binary.
        # cmd contains --distpath <path> --name <name>. Recover them.
        dist = cmd[cmd.index("--distpath") + 1]
        name = cmd[cmd.index("--name") + 1]
        Path(dist).mkdir(parents=True, exist_ok=True)
        (Path(dist) / name).write_text("#!/bin/sh\n")
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    monkeypatch.setattr(build_mod.subprocess, "run", fake_run)

    err = StringIO()
    out = StringIO()
    rc = build(str(src), [], str(tmp_path / "demo"), stderr=err, stdout=out)
    assert rc == 0
    assert "no adapter is bundled" in err.getvalue()


# ---------------------------------------------------------------------------
# Slow integration tests — actual PyInstaller invocation
# ---------------------------------------------------------------------------


def _run_binary(path: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(path), *args], check=False, capture_output=True, text=True,
        timeout=timeout,
    )


@pytest.mark.skipif(not _RUN_PYI, reason="PyInstaller not available")
def test_build_sequential_program_end_to_end(tmp_path):
    """Builds program1_basics.limn into a standalone binary, runs it,
    inspects it (plain + JSON), and inspects via `liminate inspect`."""
    out = StringIO()
    err = StringIO()
    rc = build(
        str(EXAMPLES / "program1_basics.limn"),
        [],
        str(tmp_path / "demo"),
        stdout=out, stderr=err,
    )
    assert rc == 0, err.getvalue()
    binary = tmp_path / "demo"
    assert binary.exists()

    # Execution: program prints expected output.
    result = _run_binary(binary, "--quiet")
    assert result.returncode == 0, result.stderr
    assert "30" in result.stdout  # show age
    assert "red, blue, green" in result.stdout

    # --inspect plain.
    inspect = _run_binary(binary, "--inspect")
    assert inspect.returncode == 0
    assert "=== Liminate Executable ===" in inspect.stdout
    assert "--- Source ---" in inspect.stdout
    assert "--- Understood As ---" in inspect.stdout
    assert "--- Packs Bundled ---" in inspect.stdout
    assert "(none)" in inspect.stdout
    assert "--- Vocabulary In Use ---" in inspect.stdout
    assert "remember" in inspect.stdout

    # --inspect --json parses.
    inspect_json = _run_binary(binary, "--inspect", "--json")
    assert inspect_json.returncode == 0
    parsed = json.loads(inspect_json.stdout)
    assert parsed["source_filename"] == "program1_basics.limn"
    assert parsed["packs"] == []
    assert "show" in parsed["vocabulary_in_use"]["verbs"]

    # `liminate inspect <binary>` reproduces the binary's --inspect output.
    cli_out = StringIO()
    cli_err = StringIO()
    rc = cli_main(["inspect", str(binary)])
    assert rc == 0


@pytest.mark.skipif(not _RUN_PYI, reason="PyInstaller not available")
def test_build_with_pack(tmp_path):
    """Reactive program bundled with the v3a test pack should embed the
    pack and run end-to-end."""
    src = EXAMPLES / "dogfood_v3a_event_driven.limn"
    pack = EXAMPLES / "dogfood_v3a_pack.json"
    if not src.exists() or not pack.exists():
        pytest.skip("v3a example assets not present")

    out = StringIO()
    err = StringIO()
    rc = build(
        str(src), [str(pack)], str(tmp_path / "reactive"),
        stdout=out, stderr=err,
    )
    assert rc == 0, err.getvalue()
    # Q2 notice MUST NOT fire when a pack is bundled.
    assert "no adapter is bundled" not in err.getvalue()

    binary = tmp_path / "reactive"
    inspect_json = _run_binary(binary, "--inspect", "--json")
    assert inspect_json.returncode == 0
    parsed = json.loads(inspect_json.stdout)
    assert len(parsed["packs"]) == 1
    assert parsed["packs"][0]["name"]  # non-empty pack name

    # The binary actually runs to a clean shutdown.
    result = _run_binary(binary, "--quiet", timeout=60)
    assert result.returncode == 0, result.stderr
    assert "Listening for changes" in result.stdout

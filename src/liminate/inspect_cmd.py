"""Branch G Phase C — `liminate inspect` and the shared manifest formatter.

The same four-section manifest surfaces in two places (Q3 §12):
- On the built binary itself: `./myapp --inspect` (the embedded entry
  script in build.py calls `format_manifest` directly).
- Via the Liminate CLI without re-executing: `liminate inspect <binary>`
  shells out to `<binary> --inspect [--json]` and re-prints stdout.

The shell-out approach satisfies the §12 requirement that inspection not
execute the program: the binary's argv handler dispatches to the inspect
path before it ever touches the embedded source.

Format (plain text, primary):

    === Liminate Executable ===
    Version: Liminate <version>
    Source: <source_filename>
    Topic: <about-topic>          (only when an `about` declaration is present)

    --- Source ---
    <verbatim>

    --- Understood As ---
    <one canonical line per statement>

    --- Packs Bundled ---
    <name, vocabulary, verbs per pack, or "(none)">

    --- Vocabulary In Use ---
    Verbs: ...
    Connectives: ...
    Operators: ...

JSON format (--json): the manifest dict produced by build.BuildManifest.
Schema versioning (D-Q4) is deliberately deferred.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def format_manifest(manifest: dict[str, Any], *, as_json: bool = False) -> str:
    """Render a manifest dict as plain text or JSON."""
    if as_json:
        return json.dumps(manifest, indent=2, ensure_ascii=False)
    return _format_plain(manifest)


def _format_plain(m: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.append("=== Liminate Executable ===")
    parts.append(f"Version: Liminate {m.get('liminate_version', '?')}")
    parts.append(f"Source: {m.get('source_filename', '?')}")
    # Meta-Structural Era: the `about` declaration's topic, when present.
    topic = m.get("topic")
    if topic:
        parts.append(f"Topic: {topic}")
    parts.append("")
    parts.append("--- Source ---")
    parts.append(m.get("source_text", "").rstrip("\n"))
    parts.append("")
    parts.append("--- Understood As ---")
    for line in m.get("canonical", []) or []:
        parts.append(line)
    parts.append("")
    parts.append("--- Packs Bundled ---")
    packs = m.get("packs") or []
    if not packs:
        parts.append("(none)")
    else:
        for p in packs:
            parts.append(f"- {p.get('name', '?')}")
            vocab = p.get("vocabulary") or []
            if vocab:
                words = ", ".join(f"{w} ({c})" for w, c in vocab)
                parts.append(f"    vocabulary: {words}")
            else:
                parts.append("    vocabulary: (none)")
            verbs = p.get("verbs") or []
            if verbs:
                parts.append("    verbs:")
                for v in verbs:
                    parts.append(f"      - {_format_verb(v)}")
            else:
                parts.append("    verbs: (none)")
    parts.append("")
    parts.append("--- Vocabulary In Use ---")
    voc = m.get("vocabulary_in_use") or {}
    parts.append(f"Verbs: {_csv(voc.get('verbs'))}")
    parts.append(f"Connectives: {_csv(voc.get('connectives'))}")
    parts.append(f"Operators: {_csv(voc.get('operators'))}")
    return "\n".join(parts)


def _csv(items: list[str] | None) -> str:
    if not items:
        return "(none)"
    return ", ".join(items)


def _format_verb(v: dict[str, Any]) -> str:
    word = v.get("word", "?")
    slots = v.get("slots") or []
    if not slots:
        return word
    slot_strs = []
    for s in slots:
        conn = s.get("connective", "")
        nm = s.get("name", "")
        tc = s.get("type_constraint")
        piece = f"{conn} <{nm}>" if conn else f"<{nm}>"
        if tc:
            piece += f":{tc}"
        slot_strs.append(piece)
    return f"{word} {' '.join(slot_strs)}"


# ---------------------------------------------------------------------------
# `liminate inspect <binary>` — shell out to the binary's own --inspect
# ---------------------------------------------------------------------------


def inspect_binary(
    binary_path: str,
    *,
    as_json: bool = False,
    stdout=None,
    stderr=None,
) -> int:
    """Print the manifest embedded in a Liminate-built binary.

    Implementation: invoke `<binary_path> --inspect [--json]`. The binary's
    argv handler short-circuits before touching the embedded program
    source, so no execution occurs. We re-print its stdout verbatim so
    JSON output remains machine-parseable.
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    path = Path(binary_path)
    if not path.exists():
        err.write(f"Error: binary not found: {binary_path}\n")
        return 2

    cmd = [str(path.resolve()), "--inspect"]
    if as_json:
        cmd.append("--json")
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except OSError as e:
        err.write(f"Error: failed to invoke binary: {e}\n")
        return 2
    if proc.stdout:
        out.write(proc.stdout)
        if not proc.stdout.endswith("\n"):
            out.write("\n")
    if proc.stderr:
        err.write(proc.stderr)
    return proc.returncode

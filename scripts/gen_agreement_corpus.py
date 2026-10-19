#!/usr/bin/env python3
"""Generate the agreement test set from this implementation.

An *agreement* is a small Liminate program of facts and `forbid` / `require` /
`permit` rules. It is how a product states a floor ("a phone number in a public
note is not allowed") in one file that several runtimes read. The Python package
is the only complete interpreter; `@liminate/ts-validator` and `liminate-swift`
carry a port of just the agreement subset, so a product can evaluate the same
file on a server and on a phone.

Two ports of one subset drift unless something outside both of them says what
the subset does. This is that something: each program in the corpus is run
through the reference interpreter, and what it did is written down. A port
passes only by reproducing those recorded outcomes, never by agreeing with
expectations a person typed beside its own code.

The subset is exactly: `about`, `--` comments, `remember a number|text|truth
called <name> with <value>`, and `forbid|require|permit <condition> [unless
<condition>] because "<text>"`. Conditions are the comparisons the analyzer
accepts there, joined by `and` / `or`.

What is recorded for each program:

    exit      the reference CLI's exit code (`--quiet --test`)
    stdout    its standard output, verbatim
    outcome   "pass"    nothing was crossed and nothing went wrong
              "crossed" at least one `forbid` was violated or `require` unmet,
                        and nothing else went wrong
              "error"   any line the interpreter rejected (a parse error, an
                        unknown name, a type it will not compare): never a pass
    crossed   for each violated rule, in program order: its verb, the rule's
              condition in canonical form, and its `because` text. Empty for
              "pass" and for "error"

`because` does not appear in the interpreter's output, so it is read from the
rule's own line; the line is found by running the program through `run()`,
which reports a result per source line, and every violation `run()` reports
must equal a line the CLI printed. If the two ever disagree this script stops
rather than write a corpus that one of them would contradict.

Usage:
    python3 scripts/gen_agreement_corpus.py > tests/fixtures/agreement-<version>.json
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from liminate.result import ResultStatus  # noqa: E402
from liminate.run import run  # noqa: E402

CORPUS_PATH = ROOT / "tests" / "fixtures" / "agreement_corpus.txt"

_BECAUSE = re.compile(r'\s+because\s+"((?:[^"\\]|\\.)*)"\s*$')
_VIOLATION = "Error: Prohibition violated: "
_UNMET = "Error: Requirement not met: "


def language_version() -> str:
    """The version of the source being read, not of whatever is installed."""
    for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("pyproject.toml states no version")


def read_corpus() -> list[dict]:
    """A case is a `# ` line naming it, then the program's lines.

    Blank lines inside a case are kept: a comment or blank line is part of what
    the interpreter reads. A program ends at the next `# ` header.
    """
    cases: list[dict] = []
    name: str | None = None
    lines: list[str] = []

    def close() -> None:
        if name is not None:
            while lines and not lines[-1].strip():
                lines.pop()
            cases.append({"id": name, "program": "\n".join(lines) + "\n"})

    for raw in CORPUS_PATH.read_text(encoding="utf-8").splitlines():
        if raw.startswith("# "):
            close()
            name, lines = raw[2:].strip(), []
        elif name is not None:
            lines.append(raw)
    close()
    return cases


def run_cli(program: str) -> tuple[int, str]:
    """The reference CLI, `--quiet --test`, on this tree's source."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "agreement.limn"
        path.write_text(program, encoding="utf-8")
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        done = subprocess.run(
            [sys.executable, "-m", "liminate", "--quiet", "--test", str(path)],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
            check=False,
        )
    return done.returncode, done.stdout


def because_of(source: str | None) -> str:
    match = _BECAUSE.search(source or "")
    return match.group(1) if match else ""


def classify(program: str, exit_code: int, stdout: str) -> tuple[str, list[dict]]:
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    printed = [ln for ln in lines if ln.startswith((_VIOLATION, _UNMET))]
    other_errors = [
        ln for ln in lines if ln.startswith("Error:") and ln not in printed
    ]

    structured = []
    for result in run(program, auto_confirm_amber=True).results:
        if result.status in (
            ResultStatus.PROHIBITION_VIOLATED,
            ResultStatus.REQUIREMENT_NOT_MET,
        ):
            meta = result.metadata or {}
            structured.append(
                {
                    "verb": meta["verb"],
                    "condition": meta["condition"],
                    "because": because_of(result.source),
                    "_line": "Error: " + (result.message or ""),
                }
            )
    if [s["_line"] for s in structured] != printed:
        raise SystemExit(
            "run() and the CLI disagree about which rules were crossed:\n"
            f"  run(): {[s['_line'] for s in structured]}\n"
            f"  CLI:   {printed}\n"
            f"  program:\n{program}"
        )
    if other_errors:
        return "error", []
    if printed:
        return "crossed", [{k: v for k, v in s.items() if k != "_line"} for s in structured]
    if exit_code != 0:
        raise SystemExit(f"exit {exit_code} with no error line:\n{stdout}\n{program}")
    return "pass", []


def main() -> None:
    cases = []
    for case in read_corpus():
        exit_code, stdout = run_cli(case["program"])
        outcome, crossed = classify(case["program"], exit_code, stdout)
        cases.append(
            {
                "id": case["id"],
                "program": case["program"],
                "exit": exit_code,
                "outcome": outcome,
                "crossed": crossed,
                "stdout": stdout,
            }
        )
    json.dump(
        {
            "language_version": language_version(),
            "generator": "scripts/gen_agreement_corpus.py",
            "surface": "about, comments, remember number|text|truth, forbid|require|permit [unless] because",
            "cases": cases,
        },
        sys.stdout,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate the behavioural conformance corpus from this implementation.

The Python package is the authority; `@liminate/ts-validator` is a hand-written
port of five of its stages. The existing parity gate compares the two
implementations' *reserved-word lists* against a frozen fixture — which is why
it stayed green while three minor versions of behaviour diverged. Adding `date`
to `_require_comparable` (v29, Calendar Era) changed what programs are accepted
and changed no word at all, so a word-list gate could not see it. Downstream,
`commongage` carried a code comment recording "a DATE RANGE cannot be written in
a Liminate sentence at this language version" for two months after it could.

This emits what a word list cannot: for each program in the corpus, what the
validation pipeline actually does with it.

The pipeline mirrored here is exactly the one the TypeScript package assembles
in `_run_line` — tokenize, reorder, parse, analyze, render — and stops where it
stops. No execution: the port has no interpreter, so runtime behaviour is not a
parity surface and is deliberately not recorded.

Its boundary, stated rather than left to be discovered: this is the *per-line*
surface. `validate()` wraps it with two things this corpus does not reach — the
first-line handling of `about`, and when-block buffering — so a program using
either is not a case here. They are a real parity surface and an honest gap,
not a passing one: a case that silently exercised `_run_line` instead would
report agreement about a path neither side took.

Usage:
    python3 scripts/gen_conformance_corpus.py > tests/fixtures/conformance-<version>.json
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from liminate.analyzer import analyze  # noqa: E402
from liminate.lexer import LexError, tokenize  # noqa: E402
from liminate.parser import parse  # noqa: E402
from liminate.renderer import render  # noqa: E402
from liminate.reorderer import reorder  # noqa: E402
from liminate.result import LiminateResult, ResultStatus  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "tests" / "fixtures" / "conformance_corpus.txt"


def language_version() -> str:
    """The version of the source being read, not of whatever is installed.

    `importlib.metadata.version("liminate")` answers for the installed
    distribution, which on any machine with an editable checkout and a released
    wheel is a different number from the tree this script just imported. A
    corpus labelled with the wrong version is worse than an unlabelled one: the
    port would compare itself against a file claiming a parity it never had.
    """
    for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("pyproject.toml states no version")

_ERROR_KIND = {
    ResultStatus.ERROR_PARSE: "parse",
    ResultStatus.ERROR_SEMANTIC: "semantic",
}


def validate_line(line: str, symtab: dict, session=None) -> dict:
    """One line through the ported stages, reported the way the port reports it.

    Deliberately shaped as `ValidationResult` from the TypeScript package —
    `status`, `canonical`, `errorKind`, `errorMessage` — so a case can be
    compared field for field without either side reshaping the other's output.
    """
    try:
        tokens = tokenize(line)
    except LexError as e:
        return {"status": "error", "errorKind": "parse", "errorMessage": str(e)}
    if not tokens:
        return {"status": "success", "canonical": ""}

    reordered = reorder(tokens)
    if isinstance(reordered, LiminateResult):
        return _from_result(reordered)

    # `parse` needs the names a bareword could be: a composition call, and —
    # since v31 — a predicate application. Without them `define overdue: ...`
    # registers nothing and `is overdue` silently parses as string equality, so
    # the corpus would record equality where the language does predicate
    # application, and teach the port the wrong thing. Both sets come from the
    # session, which is where the CLI gets them.
    ast = parse(
        reordered,
        session.composition_names() if session else None,
        session.predicate_names() if session else None,
    )
    if isinstance(ast, LiminateResult):
        return _from_result(ast)

    analysis = analyze(ast, symtab)
    if isinstance(analysis, LiminateResult):
        return {**_from_result(analysis), "canonical": render(ast)}

    return {"status": "success", "canonical": render(ast), "nodes": node_kinds(ast)}


def node_kinds(node: object) -> list[str]:
    """Every AST node kind in the tree, sorted, with duplicates kept.

    The canonical rendering is not enough to compare on. `require total is
    large` and `require total is overdue` render identically — the first is a
    predicate application, the second is string equality against a bareword,
    and a port that implemented `define` as a no-op would pass a text
    comparison on both. The AST is where they differ, so the AST is what the
    corpus records.

    Kind names are the class name here and the `kind` field in TypeScript, and
    they already agree — `RequireNode` is `RequireNode` on both sides.
    """
    found: list[str] = []

    def walk(value: object) -> None:
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            found.append(type(value).__name__)
            for f in dataclasses.fields(value):
                walk(getattr(value, f.name))
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)

    walk(node)
    return sorted(found)


def _from_result(result: LiminateResult) -> dict:
    if result.status in (ResultStatus.AMBER_PRECEDENCE, ResultStatus.AMBER_AMBIGUITY):
        return {"status": "amber", "amberMessage": result.message}
    return {
        "status": "error",
        "errorKind": _ERROR_KIND.get(result.status, result.status.value),
        "errorMessage": result.message,
    }


def read_corpus() -> list[dict]:
    """Read the corpus file.

    A case is a `#` comment block naming it, then one or more program lines.
    Multi-line cases share a symbol table, because a program's later lines
    depend on what its earlier lines declared — a single-line corpus could not
    reach any condition over a remembered value, which is most of the surface
    that drifts.
    """
    cases: list[dict] = []
    name: str | None = None
    lines: list[str] = []
    for raw in CORPUS_PATH.read_text(encoding="utf-8").splitlines():
        if raw.startswith("# "):
            if name is not None and lines:
                cases.append({"id": name, "source": "\n".join(lines)})
            name, lines = raw[2:].strip(), []
        elif raw.strip():
            lines.append(raw)
    if name is not None and lines:
        cases.append({"id": name, "source": "\n".join(lines)})
    return cases


def main() -> None:
    """Validate each line, then execute it so the next line sees the state.

    The two implementations reach that state by different routes and this is
    the one place the difference has to be handled. TypeScript has no
    interpreter, so it simulates just enough with `update_symbol_table`; Python
    has one, so it runs the line. What gets *recorded* is the validation result
    either way — execution here only advances the symbol table, and its own
    statuses (a fired prohibition, a runtime error) are never written to the
    corpus, because the port cannot produce them and a parity file must not
    contain a field one side can never match.
    """
    from liminate.run import Session  # noqa: PLC0415 — keeps the import local

    cases = []
    for case in read_corpus():
        session = Session()
        results = []
        for line in case["source"].splitlines():
            result = validate_line(line, session.symtab, session)
            results.append(result)
            if result["status"] == "success":
                session.run_line(line)
        cases.append({"id": case["id"], "source": case["source"], "results": results})
    json.dump(
        {
            "language_version": language_version(),
            "generator": "scripts/gen_conformance_corpus.py",
            "surface": "tokenize -> reorder -> parse -> analyze -> render",
            "cases": cases,
        },
        sys.stdout,
        indent=2,
        sort_keys=True,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

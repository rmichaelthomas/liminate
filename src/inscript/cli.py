"""CLI wrapper for Inscript v1.

This is the ONLY module permitted to call `input()` or `print()`
(v1d §64). It is a thin layer over the structured-result pipeline:
lexer → reorderer → parser → interpreter (which gates on the analyzer
per-op). All other modules return data.

Usage:
    python -m inscript                  # Interactive REPL
    python -m inscript <file.insc>      # Execute a file
    python -m inscript --test <file>    # Test mode (auto-confirm amber)
    python -m inscript <file> --test    # --test may appear in any position
"""

from __future__ import annotations

import sys
from pathlib import Path

from .analyzer import SymbolEntry
from .interpreter import execute
from .lexer import tokenize
from .parser import parse
from .reorderer import reorder
from .result import InscriptResult, ResultStatus


# ---------------------------------------------------------------------------
# Session: the shared symbol table across statements
# ---------------------------------------------------------------------------


class Session:
    def __init__(self) -> None:
        self.symtab: dict[str, SymbolEntry] = {}

    def composition_names(self) -> set[str]:
        return {n for n, e in self.symtab.items() if e.type == "composition"}

    def run_line(self, line: str) -> InscriptResult | None:
        """Execute one source line. Returns the result, or None for blank."""
        tokens = tokenize(line)
        if not tokens:
            return None
        reordered = reorder(tokens)
        if isinstance(reordered, InscriptResult):
            return reordered
        ast = parse(reordered, composition_names=self.composition_names())
        if isinstance(ast, InscriptResult):
            # Amber outcomes carry a pending_ast for confirmation flow.
            return ast
        return execute(ast, self.symtab)


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------


def display_result(
    result: InscriptResult | None,
    session: Session,
    *,
    auto_confirm_amber: bool = False,
    out=None,
    _suppress_canonical: bool = False,
) -> None:
    """Render an InscriptResult to stdout per v1c §50 + v1a §33."""
    if result is None:
        return
    write = (out.write if out is not None else lambda s: print(s, end=""))

    if result.canonical and not _suppress_canonical:
        write(f"I understand this as: {result.canonical}\n")

    if result.status is ResultStatus.SUCCESS:
        if result.output:
            for line in result.output:
                write(f"{line}\n")
        return

    if result.status in (
        ResultStatus.AMBER_PRECEDENCE,
        ResultStatus.AMBER_AMBIGUITY,
    ):
        write(f"{result.message}\n")
        if auto_confirm_amber:
            confirm = True
        else:
            response = _prompt("Confirm? (y/n): ")
            confirm = response.strip().lower().startswith("y")
        if confirm and result.pending_ast is not None:
            new_result = execute(result.pending_ast, session.symtab)
            # The canonical was already shown above (and in the amber
            # message). Don't echo it a second time.
            display_result(
                new_result,
                session,
                auto_confirm_amber=auto_confirm_amber,
                out=out,
                _suppress_canonical=True,
            )
        return

    # ERROR_PARSE / ERROR_SEMANTIC
    write(f"Error: {result.message}\n")
    if result.output:
        # Some prior ops in a sequence may have produced output before
        # the failure — surface them so the user sees what happened.
        for line in result.output:
            write(f"{line}\n")


def _prompt(message: str) -> str:
    try:
        return input(message)
    except EOFError:
        return ""


# ---------------------------------------------------------------------------
# File + REPL drivers
# ---------------------------------------------------------------------------


def run_file(path: str, *, auto_confirm_amber: bool = False) -> None:
    session = Session()
    content = Path(path).read_text(encoding="utf-8")
    for line in content.splitlines():
        result = session.run_line(line)
        display_result(result, session, auto_confirm_amber=auto_confirm_amber)


def repl() -> None:
    session = Session()
    print("Inscript v1 — type 'exit' to quit.")
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if line.strip().lower() in ("exit", "quit"):
            return
        result = session.run_line(line)
        display_result(result, session)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    auto = False
    # Accept --test in any position. Unknown flags (starting with --) are
    # rejected so typos don't silently change behavior.
    positional: list[str] = []
    for a in args:
        if a == "--test":
            auto = True
        elif a.startswith("--"):
            print(f"Error: unknown flag '{a}'", file=sys.stderr)
            return 2
        else:
            positional.append(a)
    if positional:
        run_file(positional[0], auto_confirm_amber=auto)
    else:
        repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

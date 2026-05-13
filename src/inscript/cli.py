"""CLI wrapper for Inscript v1 / v2c / v2d / v3a.

This is the ONLY module permitted to call `input()` or `print()`
(v1d §64). It is a thin layer over the structured-result pipeline:
lexer → reorderer → parser → interpreter (which gates on the analyzer
per-op). All other modules return data.

Usage:
    python -m inscript                  # Interactive REPL
    python -m inscript <file.insc>      # Execute a file
    python -m inscript --test <file>    # Test mode (auto-confirm amber)
    python -m inscript <file> --test    # --test may appear in any position
    python -m inscript <file> --quiet   # Suppress "I understand this as: ..."
                                        # echo; mirror blank source lines so
                                        # visual grouping survives. U1/U4.

v3a additions:
- Session owns a HandlerTable (registered `when` handlers) and a
  LiveValueRegistry (declared live values + their lifecycle status).
- Domain packs are passed at Session construction (Phase 10 adds the
  `--pack` flag to wire them up from the CLI).
- Phase 1 sequential execution registers `when` handlers but does not
  fire them. Phase 2 entry (Phase 9/10) drains the adapter queue and
  yields HANDLER_FIRE / SHUTDOWN results.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .adapter import DomainPack, LiveValueRegistry, TestDomainPack
from .analyzer import SymbolEntry
from .interpreter import HandlerTable, execute
from .lexer import LexError, leading_indent, tokenize
from .listener import listen
from .packs.timer import make_timer_pack
from .parser import parse, parse_when_block
from .reorderer import reorder
from .result import InscriptResult, ResultStatus
from .vocabulary import TokenType


# ---------------------------------------------------------------------------
# Session: the shared symbol table across statements (+ v3a listener state)
# ---------------------------------------------------------------------------


class Session:
    def __init__(
        self,
        *,
        domain_packs: list[DomainPack] | None = None,
    ) -> None:
        self.symtab: dict[str, SymbolEntry] = {}
        # v3a §108 / §117 / §118 — listener-mode state.
        self.handler_table = HandlerTable()
        self.live_value_registry = LiveValueRegistry()
        self.domain_packs: list[DomainPack] = list(domain_packs or [])
        # Phase 1 error accumulator: if any sequential statement produced
        # ERROR_PARSE, ERROR_SEMANTIC, or an unresolved AMBER, the gate
        # (§107) blocks Phase 2. The CLI populates this via run_line's
        # caller — record_result is the integration point.
        self.phase1_had_error: bool = False

        # Register declared live values from each pack. Names become
        # visible in the symbol table before Phase 1 begins so `when`
        # condition resolution (§108) can see them.
        for pack in self.domain_packs:
            for decl in pack.declarations():
                self.live_value_registry.declare(decl, pack.name())
                if decl.name not in self.symtab:
                    self.symtab[decl.name] = SymbolEntry(
                        name=decl.name,
                        value=None,
                        type=decl.value_type,
                    )

    def composition_names(self) -> set[str]:
        return {n for n, e in self.symtab.items() if e.type == "composition"}

    def run_line(self, line: str) -> InscriptResult | None:
        """Execute one source line. Returns the result, or None for blank."""
        try:
            tokens = tokenize(line)
        except LexError as e:
            # v2c §86/§92 — unclosed or empty quoted strings surface as
            # ERROR_PARSE (Outcome 4 per v1c §50).
            return InscriptResult(
                status=ResultStatus.ERROR_PARSE,
                message=e.message,
                executed=False,
            )
        if not tokens:
            return None
        reordered = reorder(tokens)
        if isinstance(reordered, InscriptResult):
            return reordered
        ast = parse(reordered, composition_names=self.composition_names())
        if isinstance(ast, InscriptResult):
            # Amber outcomes carry a pending_ast for confirmation flow.
            return ast
        return execute(
            ast, self.symtab,
            handler_table=self.handler_table,
            live_value_registry=self.live_value_registry,
        )

    def run_when_block(
        self,
        header_line: str,
        action_lines: list[str],
    ) -> InscriptResult | None:
        """Execute a v3a `when` block — header line plus its already-
        de-indented action lines.

        The caller (run_file) is responsible for indentation validation
        (§110): tabs, deeper-than-block, empty block. By the time we
        get here, `action_lines` is a list of action statement strings
        with leading whitespace stripped — they tokenize and parse like
        any other line.
        """
        try:
            header_tokens = tokenize(header_line)
        except LexError as e:
            return InscriptResult(
                status=ResultStatus.ERROR_PARSE,
                message=e.message,
                executed=False,
            )
        header_reordered = reorder(header_tokens)
        if isinstance(header_reordered, InscriptResult):
            return header_reordered

        action_token_lists: list = []
        for raw in action_lines:
            try:
                toks = tokenize(raw)
            except LexError as e:
                return InscriptResult(
                    status=ResultStatus.ERROR_PARSE,
                    message=e.message,
                    executed=False,
                )
            if not toks:
                continue  # blank line inside the block — v1c §48
            re_ordered = reorder(toks)
            if isinstance(re_ordered, InscriptResult):
                return re_ordered
            action_token_lists.append(re_ordered)

        ast = parse_when_block(
            header_reordered, action_token_lists,
            composition_names=self.composition_names(),
        )
        if isinstance(ast, InscriptResult):
            return ast
        return execute(
            ast, self.symtab,
            handler_table=self.handler_table,
            live_value_registry=self.live_value_registry,
        )

    def adapters(self):
        """Return the adapter for each registered domain pack, in pack
        registration order."""
        return [pack.adapter() for pack in self.domain_packs]

    def record_result(self, result: InscriptResult | None) -> None:
        """Track whether Phase 1 had any blocking outcomes (v3a §107).

        Called by the display layer after each result so the Session can
        decide whether to enter Phase 2 once the source is exhausted.
        ERROR_PARSE, ERROR_SEMANTIC, and unresolved-AMBER outcomes set
        the gate; SUCCESS does not. Resolved amber clears nothing —
        once an amber is confirmed, the display layer feeds the
        replacement SUCCESS/ERROR result back through this hook."""
        if result is None:
            return
        if result.status in (
            ResultStatus.ERROR_PARSE,
            ResultStatus.ERROR_SEMANTIC,
            ResultStatus.AMBER_PRECEDENCE,
            ResultStatus.AMBER_AMBIGUITY,
        ):
            self.phase1_had_error = True


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------


_TRUNCATION_THRESHOLD = 20  # U5: lists longer than this are truncated on auto-show.


def _is_auto_shown(canonical: str | None) -> bool:
    """U5: only auto-show outputs are subject to truncation.

    Explicit `show <name>` and `each ... show <field>` are user-requested
    displays — truncating them would violate intent. The auto-show
    sources that can produce >20-item output are `gather` and `keep`.
    `count` and `combine` produce single-value output that can't exceed
    the threshold; checking them is harmless but unnecessary.
    """
    if not canonical:
        return False
    return canonical.startswith("gather ") or canonical.startswith("keep ")


def _maybe_truncate(lines: list[str]) -> list[str]:
    """U5: condense large auto-show output.

    Two display shapes are produced by the interpreter (v1b §42):
    - Single line of comma-separated items (numeric or string list).
    - Multiple lines, one record per line (list of records).

    For either shape exceeding 20 items, keep the first 10 and the last
    10 with an ellipsis between them. Truncation is display-only — the
    symbol table holds the full list.
    """
    if not lines:
        return lines
    if len(lines) > _TRUNCATION_THRESHOLD:
        return lines[:10] + ["..."] + lines[-10:]
    if len(lines) == 1 and ", " in lines[0]:
        parts = lines[0].split(", ")
        if len(parts) > _TRUNCATION_THRESHOLD:
            head = ", ".join(parts[:10])
            tail = ", ".join(parts[-10:])
            return [f"{head}, ..., {tail}"]
    return lines


def display_result(
    result: InscriptResult | None,
    session: Session,
    *,
    auto_confirm_amber: bool = False,
    quiet: bool = False,
    out=None,
    _suppress_canonical: bool = False,
) -> None:
    """Render an InscriptResult to stdout per v1c §50 + v1a §33.

    When `quiet` is True (U1/U4), the "I understand this as: ..." echo
    is suppressed. Data output, error messages, and amber prompts still
    render. The interpreter's structured result is unchanged — quiet
    only affects what reaches stdout.
    """
    if result is None:
        return
    write = (out.write if out is not None else lambda s: print(s, end=""))

    if result.canonical and not _suppress_canonical and not quiet:
        write(f"I understand this as: {result.canonical}\n")

    if result.status is ResultStatus.SUCCESS:
        if result.output:
            lines = (
                _maybe_truncate(result.output)
                if _is_auto_shown(result.canonical)
                else result.output
            )
            for line in lines:
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
                quiet=quiet,
                out=out,
                _suppress_canonical=True,
            )
        return

    # v3a §122 — listener-mode statuses.
    if result.status is ResultStatus.LISTENING:
        watching = (result.metadata or {}).get("watching", [])
        if watching:
            write(f"Listening for changes to: {', '.join(watching)}\n")
        else:
            write("Listening for changes.\n")
        return
    if result.status is ResultStatus.HANDLER_FIRE:
        # v3a §122: HANDLER_FIRE wraps each successful action-block
        # statement result. The output is displayed identically to
        # SUCCESS.
        if result.output:
            lines = (
                _maybe_truncate(result.output)
                if _is_auto_shown(result.canonical)
                else result.output
            )
            for line in lines:
                write(f"{line}\n")
        return
    if result.status is ResultStatus.SHUTDOWN:
        if result.output:
            for line in result.output:
                write(f"{line}\n")
        return
    if result.status is ResultStatus.ERROR_RUNTIME:
        write(f"Error: {result.message}\n")
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


def run_file(
    path: str,
    *,
    auto_confirm_amber: bool = False,
    quiet: bool = False,
    domain_packs: list[DomainPack] | None = None,
    out=None,
) -> None:
    """Execute an Inscript source file (Phase 1 + optional Phase 2).

    Phase 1 reads the file line-by-line. Top-level `when` lines start
    an indentation-aware block: subsequent indented lines belong to
    the action block (v3a §110). After Phase 1 completes, if any
    handlers registered and Phase 1 had no errors, Phase 2 enters
    listener mode (§107).
    """
    session = Session(domain_packs=domain_packs)
    content = Path(path).read_text(encoding="utf-8")
    write = (out.write if out is not None else lambda s: print(s, end=""))
    lines = content.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]

        # v1c §48 — blank lines are skipped by the lexer. --quiet mirrors
        # them so the user's paragraph breaks survive (U1/U4).
        if not line.strip():
            if quiet:
                write("\n")
            i += 1
            continue

        # Tab-in-leading-whitespace is a v3a §110 lex error — surface it
        # as ERROR_PARSE and skip this line.
        try:
            indent = leading_indent(line)
        except LexError as e:
            err = InscriptResult(
                status=ResultStatus.ERROR_PARSE,
                message=e.message,
                executed=False,
            )
            display_result(
                err, session,
                auto_confirm_amber=auto_confirm_amber, quiet=quiet, out=out,
            )
            session.record_result(err)
            i += 1
            continue

        # Detect a `when` block at indent 0. A line is a `when` header
        # iff its first token is the `when` CONNECTIVE — we use the
        # lexer rather than a string prefix check so quoted `"when"` or
        # similar edge cases don't trip the detector.
        is_when_header = False
        if indent == 0:
            try:
                header_tokens = tokenize(line)
            except LexError:
                header_tokens = []
            if (
                header_tokens
                and header_tokens[0].type is TokenType.CONNECTIVE
                and header_tokens[0].value == "when"
            ):
                is_when_header = True

        if is_when_header:
            i = _consume_when_block(
                lines, i, session,
                auto_confirm_amber=auto_confirm_amber,
                quiet=quiet,
                out=out,
                write=write,
            )
            continue

        # Regular Phase 1 sequential statement.
        result = session.run_line(line)
        display_result(
            result, session,
            auto_confirm_amber=auto_confirm_amber,
            quiet=quiet,
            out=out,
        )
        session.record_result(result)
        i += 1

    # v3a §107 — Phase 2 gate: only enter listener mode if Phase 1 had
    # zero errors AND at least one handler registered. Otherwise the
    # source executed as a regular v2d program (or reported Phase 1
    # errors that the user must fix before listening can begin).
    if session.handler_table.is_empty():
        return
    if session.phase1_had_error:
        # Don't even yield a SHUTDOWN — the existing error stream is the
        # user's signal that Phase 2 didn't start. The condition is
        # rare in practice: most programs that contain `when` blocks are
        # error-free Phase 1 setup.
        return

    # Phase 2 streams results from the listener generator. v3a §122
    # data (HANDLER_FIRE output, SHUTDOWN message, errors) is always
    # rendered regardless of --quiet — display_result itself only gates
    # the "I understand this as: ..." canonical echo on `quiet`, which
    # we honor consistently here for Phase 2 too (canonical echo would
    # be noise for HANDLER_FIRE — the user already confirmed the source
    # at registration time).
    adapters = session.adapters()
    for result in listen(
        session.symtab,
        session.handler_table,
        session.live_value_registry,
        adapters,
    ):
        display_result(
            result, session,
            auto_confirm_amber=auto_confirm_amber,
            quiet=quiet,
            out=out,
        )


def _consume_when_block(
    lines: list[str],
    start_idx: int,
    session: Session,
    *,
    auto_confirm_amber: bool,
    quiet: bool,
    out,
    write,
) -> int:
    """Buffer the indented action block starting at line index
    `start_idx + 1` and dispatch the full when-block to the session.

    Returns the next index to process. On indentation errors (tabs in
    a continuation line, indent deeper than the established depth)
    emits ERROR_PARSE; on empty blocks the parser surfaces the
    canonical §110 wording.
    """
    header_line = lines[start_idx]
    action_lines: list[str] = []
    block_depth: int | None = None
    block_error: str | None = None
    consumed_through = start_idx  # last index we've "claimed"
    j = start_idx + 1

    while j < len(lines):
        next_line = lines[j]
        # Blank lines inside the block are skipped (v1c §48 / v3a §110).
        if not next_line.strip():
            if quiet:
                write("\n")
            consumed_through = j
            j += 1
            continue
        try:
            next_indent = leading_indent(next_line)
        except LexError as e:
            block_error = e.message
            consumed_through = j  # claim the bad line so the outer loop skips it
            j += 1
            break
        if next_indent == 0:
            # Block ends at a top-level line — leave it for the outer loop.
            break
        # First indented line sets the block's depth.
        if block_depth is None:
            block_depth = next_indent
        elif next_indent > block_depth:
            block_error = (
                f"This line is indented {next_indent} spaces, deeper than "
                f"the action block's first indented line ({block_depth} "
                f"spaces). v3a §110 — all action lines in a 'when' block "
                f"must use the same indentation depth."
            )
            consumed_through = j
            j += 1
            break
        elif next_indent < block_depth:
            # Shallower-but-non-zero ends the block; leave the line for
            # the outer loop to process as a top-level statement.
            break
        action_lines.append(next_line.lstrip(" "))
        consumed_through = j
        j += 1

    if block_error is not None:
        err = InscriptResult(
            status=ResultStatus.ERROR_PARSE,
            message=block_error,
            executed=False,
        )
        display_result(
            err, session,
            auto_confirm_amber=auto_confirm_amber, quiet=quiet, out=out,
        )
        session.record_result(err)
        return consumed_through + 1

    result = session.run_when_block(header_line, action_lines)
    display_result(
        result, session,
        auto_confirm_amber=auto_confirm_amber,
        quiet=quiet,
        out=out,
    )
    session.record_result(result)
    return j  # j points to the first un-consumed line


def repl() -> None:
    session = Session()
    print("Inscript v3a — type 'exit' to quit.")
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


def _make_test_pack(
    config: dict, *, default_name: str = "pack",
) -> TestDomainPack:
    """Factory for the existing `type == "test"` pack (default)."""
    declarations = [(d[0], d[1]) for d in config.get("declarations", [])]
    script: list = []
    for entry in config.get("script", []):
        if isinstance(entry, str) and entry == "[done]":
            script.append("[done]")
        elif isinstance(entry, list) and len(entry) == 2:
            script.append((entry[0], entry[1]))
        else:
            raise ValueError(
                f"malformed script entry {entry!r} — each entry must "
                f"be ['name', value] or '[done]'."
            )
    return TestDomainPack(
        declarations=declarations,
        script=script,
        name=config.get("name", default_name),
    )


# Pack-type dispatch table for the --pack CLI flag. Adding a new pack
# means adding its factory here (and importing it at the top of the
# module).
_PACK_FACTORIES = {
    "test": _make_test_pack,
    "timer": lambda config, **_kw: make_timer_pack(config),
}


def load_pack_from_arg(arg: str) -> DomainPack:
    """Load a domain pack from a CLI `--pack` argument.

    `arg` may be either:
      - An inline JSON string (starts with `{`), or
      - A path to a JSON config file.

    The decoded JSON object's optional `"type"` field selects the
    pack factory; the default is `"test"` for backward compatibility
    with existing dogfood pack JSON files.
    """
    arg_stripped = arg.strip()
    if arg_stripped.startswith("{"):
        config = json.loads(arg_stripped)
        default_name = "pack"
    else:
        config = json.loads(Path(arg).read_text(encoding="utf-8"))
        default_name = Path(arg).stem
    pack_type = config.get("type", "test")
    factory = _PACK_FACTORIES.get(pack_type)
    if factory is None:
        raise ValueError(
            f"unknown pack type '{pack_type}'. "
            f"Allowed: {sorted(_PACK_FACTORIES)}."
        )
    return factory(config, default_name=default_name)


def load_pack_from_path(path: str) -> DomainPack:
    """Backwards-compatible shim — `load_pack_from_arg` for an arg
    known to be a file path."""
    return load_pack_from_arg(path)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    auto = False
    quiet = False
    pack_paths: list[str] = []
    positional: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--test":
            auto = True
        elif a == "--quiet":
            quiet = True
        elif a == "--pack":
            # `--pack <arg>` registers a domain pack. `<arg>` may be
            # either a JSON file path or an inline JSON string (starts
            # with `{`). The decoded config's optional `"type"` field
            # selects the pack factory; `"test"` is the default for
            # backward compatibility. Multiple `--pack` flags accumulate.
            if i + 1 >= len(args):
                print(
                    "Error: --pack requires an argument (JSON file path or inline JSON)",
                    file=sys.stderr,
                )
                return 2
            pack_paths.append(args[i + 1])
            i += 1
        elif a.startswith("--pack="):
            pack_paths.append(a[len("--pack="):])
        elif a.startswith("--"):
            print(f"Error: unknown flag '{a}'", file=sys.stderr)
            return 2
        else:
            positional.append(a)
        i += 1

    domain_packs: list[DomainPack] = []
    for p in pack_paths:
        try:
            domain_packs.append(load_pack_from_arg(p))
        except (OSError, ValueError, json.JSONDecodeError) as e:
            print(f"Error loading pack '{p}': {e}", file=sys.stderr)
            return 2

    if positional:
        run_file(
            positional[0],
            auto_confirm_amber=auto,
            quiet=quiet,
            domain_packs=domain_packs or None,
        )
    else:
        repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

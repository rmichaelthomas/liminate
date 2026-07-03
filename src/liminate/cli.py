"""CLI wrapper for Liminate v1 / v2c / v2d / v3a.

This is the ONLY module permitted to call `input()` or `print()`
(v1d §64). It is a thin layer over the structured-result pipeline:
lexer → reorderer → parser → interpreter (which gates on the analyzer
per-op). All other modules return data.

Usage:
    liminate                            # Interactive REPL
    liminate <file.limn>                # Execute a file
    liminate --test <file>              # Test mode (auto-confirm amber)
    liminate <file> --test              # --test may appear in any position
    liminate <file> --quiet             # Suppress "I understand this as: ..."
                                        # echo; mirror blank source lines so
                                        # visual grouping survives. U1/U4.
    liminate <file> --verbose           # Emit per-line execution metadata
                                        # (JSON to stderr). Combinable with
                                        # --quiet for headless pipeline mode.
    liminate --version                  # Print "Liminate <version>" and exit.

`python -m liminate` is the equivalent module-invocation form and works
in every position above.

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
from importlib.metadata import version as _pkg_version
from pathlib import Path

from .adapter import (
    DomainPack,
    TestDomainPack,
    parse_pack_verb_signature,
)
from .interpreter import execute
from .packs.file_watcher import make_file_watcher_pack
from .packs.stdin import make_stdin_pack
from .packs.timer import make_timer_pack
from .result import LiminateResult, ResultStatus
# The program-execution loop and Session live in `run` (v11 §22). `cli`
# depends on `run`, never the reverse. Session is re-exported here for the
# REPL and for tests that import `liminate.cli.Session`.
from .run import (  # noqa: F401  (Session/ContractResult re-exported)
    ContractResult,
    Session,
    run as run_program,
)
from .run import _consume_when_block as _run_consume_when_block


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------


_TRUNCATION_THRESHOLD = 20  # U5: lists longer than this are truncated on auto-show.


def _format_trigger_tag(metadata: dict | None) -> str:
    """U2 — compact tag describing why a handler fired.

    `[initial]`                       initial evaluation (§121)
    `[name → value]`                  adapter update (single name)
    `[name1, name2 → ...]`            multi-name adapter update (rare)
    `[cascade: <names> changed]`     cascaded firing (§114)
    """
    if not metadata:
        return "[handler]"
    trig = metadata.get("trigger") or {}
    source = trig.get("source")
    if source == "initial":
        return "[initial]"
    if source == "cascade":
        changed = trig.get("values_changed") or []
        if changed:
            return f"[cascade: {', '.join(changed)} changed]"
        return "[cascade]"
    if source == "adapter_update":
        changed = trig.get("values_changed") or []
        new = trig.get("new_values") or {}
        if len(changed) == 1:
            n = changed[0]
            v = new.get(n)
            return f"[{n} → {_format_trigger_value(v)}]"
        if changed:
            return f"[{', '.join(changed)} updated]"
        return "[update]"
    return f"[{source or 'handler'}]"


def _format_trigger_value(value) -> str:
    """Compact one-line stringification of an adapter-pushed value for
    the trigger tag. Numbers and short strings pass through; lists and
    records get a brief shape summary so the tag stays compact."""
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return f"<list of {len(value)}>"
    if isinstance(value, dict):
        return f"<record with {len(value)} field{'s' if len(value) != 1 else ''}>"
    return repr(value)


def _trigger_key(metadata: dict | None) -> tuple:
    """Key used to detect "same firing, next statement" — equal across
    every action-statement result in a single handler firing, distinct
    across cascaded firings (cascade source flips even when the index
    matches a prior firing)."""
    if not metadata:
        return ()
    trig = metadata.get("trigger") or {}
    return (
        trig.get("source"),
        trig.get("handler_index"),
        tuple(trig.get("values_changed") or ()),
    )


_SHUTDOWN_MESSAGES = {
    "finish": "Listener stopped: finish called.",
    "adapter_complete": "Listener stopped: all event sources completed.",
    "no_adapters": "Listener stopped: no event sources registered.",
    "error": "Listener stopped: error (see above).",
    "external": "Listener stopped: interrupted.",
}


def _is_auto_shown(canonical: str | None) -> bool:
    """U5: only auto-show outputs are subject to truncation.

    Explicit `show <name>` and `each ... show <field>` are user-requested
    displays — truncating them would violate intent. The auto-show
    sources that can produce >20-item output are `gather` and `keep`.
    `count` and `sum` produce single-value output that can't exceed
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
    result: LiminateResult | None,
    session: Session,
    *,
    auto_confirm_amber: bool = False,
    quiet: bool = False,
    out=None,
    _suppress_canonical: bool = False,
) -> None:
    """Render an LiminateResult to stdout per v1c §50 + v1a §33.

    When `quiet` is True (U1/U4), the "I understand this as: ..." echo
    is suppressed. Data output, error messages, and amber prompts still
    render. The interpreter's structured result is unchanged — quiet
    only affects what reaches stdout.
    """
    if result is None:
        return
    write = (out.write if out is not None else lambda s: print(s, end=""))

    # U1: HANDLER_FIRE is a Phase 2 reactive firing, not a Phase 1
    # canonical confirmation — suppress the "I understand this as: …"
    # echo for those results entirely. Other listener-mode statuses
    # (LISTENING / SHUTDOWN / ERROR_RUNTIME) never carry a canonical, so
    # they're unaffected.
    if (
        result.canonical
        and not _suppress_canonical
        and not quiet
        and result.status is not ResultStatus.HANDLER_FIRE
    ):
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
        session._last_trigger_key = None
        watching = (result.metadata or {}).get("watching", [])
        if watching:
            write(f"Listening for changes to: {', '.join(watching)}\n")
        else:
            write("Listening for changes.\n")
        return
    if result.status is ResultStatus.HANDLER_FIRE:
        # v3a §122 + U1/U2: HANDLER_FIRE wraps each successful action-
        # block statement result. The first output line of each distinct
        # firing is prefixed with a compact trigger tag (U2). Subsequent
        # statements in the same firing — same trigger key — omit the
        # tag so multi-statement action blocks read as a single grouped
        # event.
        if result.output:
            lines = (
                _maybe_truncate(result.output)
                if _is_auto_shown(result.canonical)
                else result.output
            )
            key = _trigger_key(result.metadata)
            for idx, line in enumerate(lines):
                if idx == 0 and key != session._last_trigger_key:
                    tag = _format_trigger_tag(result.metadata)
                    write(f"{tag} {line}\n")
                    session._last_trigger_key = key
                else:
                    write(f"{line}\n")
        return
    if result.status is ResultStatus.SHUTDOWN:
        # U3 — derive the exit-reason wording from metadata.reason so the
        # user sees WHY listener mode ended (finish vs adapter completion
        # vs error vs interrupt). The listener's `output` field is kept
        # for back-compat but the metadata-driven message is authoritative.
        session._last_trigger_key = None
        reason = (result.metadata or {}).get("reason")
        message = _SHUTDOWN_MESSAGES.get(reason)
        if message is not None:
            write(f"{message}\n")
        elif result.output:
            for line in result.output:
                write(f"{line}\n")
        return
    if result.status is ResultStatus.ERROR_RUNTIME:
        session._last_trigger_key = None
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


def _emit_verbose_metadata(
    line_num: int,
    timestamp: str,
    duration_ms: float,
    *,
    result: LiminateResult | None = None,
    verbose_out=None,
) -> None:
    metadata = {
        "line": line_num,
        "timestamp": timestamp,
        "duration_ms": duration_ms,
    }
    # Receipts v5 §15 dim. 3 — surface the contributing pack for pack verbs.
    if result is not None and result.metadata and "pack" in result.metadata:
        metadata["pack"] = result.metadata["pack"]
    print(json.dumps(metadata), file=verbose_out or sys.stderr)


# ---------------------------------------------------------------------------
# File + REPL drivers
# ---------------------------------------------------------------------------


def run_file(
    path: str,
    *,
    auto_confirm_amber: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    domain_packs: list[DomainPack] | None = None,
    out=None,
    verbose_out=None,
) -> bool:
    """Execute a Liminate source file (Phase 1 + optional Phase 2).

    Thin I/O wrapper over the shared program-execution loop `run.run()`
    (v11 §22): read the file, drive the loop, and render each result inline
    through the unchanged `display_result`. Returns True if any error
    (parse, semantic, or runtime) occurred across either phase, so callers
    can propagate a non-zero exit code.

    Display is driven inline via the `on_result` sink — not after the run —
    so interactive amber confirmation and quiet-mode blank-line mirroring
    happen at the exact loop position they always did, keeping CLI output
    byte-for-byte identical. `run()` owns `record_result`; the sink only
    renders (display + verbose metadata).
    """
    content = Path(path).read_text(encoding="utf-8")
    write = (out.write if out is not None else lambda s: print(s, end=""))

    def on_result(result, session, line_num, ts, dur):
        display_result(
            result, session,
            auto_confirm_amber=auto_confirm_amber,
            quiet=quiet,
            out=out,
        )
        if verbose and line_num is not None and result is not None:
            _emit_verbose_metadata(
                line_num, ts, dur, result=result, verbose_out=verbose_out,
            )

    on_blank = (lambda: write("\n")) if quiet else None

    result = run_program(
        content,
        domain_packs=domain_packs,
        auto_confirm_amber=auto_confirm_amber,
        on_result=on_result,
        on_blank=on_blank,
    )
    return result.had_error


def _consume_when_block(
    lines: list[str],
    start_idx: int,
    session: Session,
    *,
    auto_confirm_amber: bool,
    quiet: bool,
    out,
    write,
    verbose: bool = False,
    verbose_out=None,
) -> int:
    """Display-driving adapter over `run._consume_when_block`.

    Retained at this signature for callers (and tests) that drive a single
    when-block through the CLI display path directly. The when-block
    buffering + execution logic lives once in `run`; this shim only injects
    the display sink (so there is no duplicated loop logic in `cli`).
    """
    def emit(result, line_num, ts, dur):
        display_result(
            result, session,
            auto_confirm_amber=auto_confirm_amber, quiet=quiet, out=out,
        )
        session.record_result(result)
        if verbose and result is not None:
            _emit_verbose_metadata(
                line_num, ts, dur, result=result, verbose_out=verbose_out,
            )

    return _run_consume_when_block(
        lines, start_idx, session,
        emit=emit,
        on_blank=(lambda: write("\n")) if quiet else None,
    )


def repl() -> None:
    session = Session()
    print("Liminate v3a — type 'exit' to quit.")
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
    """Factory for the existing `type == "test"` pack (default).

    The update sequence may be supplied under either key:
      - `"sequence"` (preferred, used by the v3a domain-pack examples)
      - `"script"`   (legacy, used by `examples/dogfood_v3a_pack.json`)

    Specifying both is rejected so a typo never silently picks the
    wrong one.
    """
    if "sequence" in config and "script" in config:
        raise ValueError(
            "test pack config has both 'sequence' and 'script' keys — "
            "use only one (prefer 'sequence')."
        )
    raw_sequence = (
        config.get("sequence")
        if "sequence" in config
        else config.get("script", [])
    )
    declarations = [(d[0], d[1]) for d in config.get("declarations", [])]
    script: list = []
    for entry in raw_sequence:
        if isinstance(entry, str) and entry == "[done]":
            script.append("[done]")
        elif isinstance(entry, list) and len(entry) == 2:
            script.append((entry[0], entry[1]))
        else:
            raise ValueError(
                f"malformed sequence entry {entry!r} — each entry must "
                f"be ['name', value] or '[done]'."
            )
    # v4a §137: optional pack vocabulary and verb signatures. Packs
    # without these keys load exactly as before (backward-compatible).
    vocabulary: list[tuple[str, str]] = []
    for entry in config.get("vocabulary", []):
        if isinstance(entry, dict):
            vocabulary.append((entry["word"], entry.get("category", "noun")))
        elif isinstance(entry, list) and len(entry) == 2:
            vocabulary.append((entry[0], entry[1]))
        else:
            raise ValueError(
                f"malformed vocabulary entry {entry!r} — each entry must "
                f"be {{'word', 'category'}} or [word, category]."
            )
    verbs = [parse_pack_verb_signature(v) for v in config.get("verbs", [])]
    return TestDomainPack(
        declarations=declarations,
        script=script,
        name=config.get("name", default_name),
        vocabulary=vocabulary,
        verbs=verbs,
    )


# Pack-type dispatch table for the --pack CLI flag. Adding a new pack
# means adding its factory here (and importing it at the top of the
# module).
_PACK_FACTORIES = {
    "test": _make_test_pack,
    "timer": lambda config, **_kw: make_timer_pack(config),
    "stdin": lambda config, **_kw: make_stdin_pack(config),
    "file-watcher": lambda config, **_kw: make_file_watcher_pack(config),
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


def _run_build_subcommand(args: list[str]) -> int:
    """`liminate build <source.limn> [--pack ...] --output <name>`.

    Routed from main() when the first argv is `build`. PyInstaller is
    imported lazily inside build() so users who never invoke `build`
    don't pay the import cost (and so the package keeps loading even
    when the optional `[build]` extra isn't installed)."""
    if "--help" in args or "-h" in args:
        print("Usage: liminate build <source.limn> [--pack <json>]... --output <name>")
        return 0

    from .build import build  # late import — PyInstaller is an optional dep

    source: str | None = None
    output: str | None = None
    pack_args: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--pack":
            if i + 1 >= len(args):
                print("Error: --pack requires an argument", file=sys.stderr)
                return 2
            pack_args.append(args[i + 1])
            i += 2
            continue
        if a.startswith("--pack="):
            pack_args.append(a[len("--pack="):])
            i += 1
            continue
        if a == "--output" or a == "-o":
            if i + 1 >= len(args):
                print("Error: --output requires an argument", file=sys.stderr)
                return 2
            output = args[i + 1]
            i += 2
            continue
        if a.startswith("--output="):
            output = a[len("--output="):]
            i += 1
            continue
        if a.startswith("--"):
            print(f"Error: unknown flag '{a}'", file=sys.stderr)
            return 2
        if source is None:
            source = a
            i += 1
            continue
        print(f"Error: unexpected argument '{a}'", file=sys.stderr)
        return 2

    if source is None:
        print(
            "Usage: liminate build <source.limn> [--pack <json>]... --output <name>",
            file=sys.stderr,
        )
        return 2
    if output is None:
        # Default the output name to the source's stem.
        output = Path(source).stem or "program"

    return build(source, pack_args, output)


def _run_inspect_subcommand(args: list[str]) -> int:
    """`liminate inspect <binary> [--json]`.

    Shells out to `<binary> --inspect [--json]`. The binary's argv
    handler short-circuits before executing the embedded program."""
    if "--help" in args or "-h" in args:
        print("Usage: liminate inspect <binary> [--json]")
        return 0

    from .inspect_cmd import inspect_binary

    binary: str | None = None
    as_json = False
    for a in args:
        if a == "--json":
            as_json = True
        elif a.startswith("--"):
            print(f"Error: unknown flag '{a}'", file=sys.stderr)
            return 2
        elif binary is None:
            binary = a
        else:
            print(f"Error: unexpected argument '{a}'", file=sys.stderr)
            return 2
    if binary is None:
        print("Usage: liminate inspect <binary> [--json]", file=sys.stderr)
        return 2
    return inspect_binary(binary, as_json=as_json)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    # Branch G Phase C — `build` and `inspect` subcommands. Routed before
    # the general flag loop so they don't collide with the existing run
    # CLI's positional-argument semantics. `--version`/`--help` placed
    # before a subcommand still wins (handled below by the legacy loop).
    if args and args[0] == "build":
        return _run_build_subcommand(args[1:])
    if args and args[0] == "inspect":
        return _run_inspect_subcommand(args[1:])

    auto = False
    quiet = False
    verbose = False
    pack_paths: list[str] = []
    positional: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--test":
            auto = True
        elif a == "--quiet":
            quiet = True
        elif a == "--verbose":
            verbose = True
        elif a == "--version":
            print(f"Liminate {_pkg_version('liminate')}")
            return 0
        elif a in ("--help", "-h"):
            print(
                "Usage: liminate [options] [file.limn]\n"
                "       liminate build <file.limn> [--pack <json>]... --output <name>\n"
                "       liminate inspect <binary> [--json]\n"
                "\n"
                "Options:\n"
                "  --pack <json>   Load a domain pack (JSON file or inline JSON)\n"
                "  --test          Auto-confirm amber (ambiguous) outcomes\n"
                "  --quiet         Suppress 'I understand this as:' echo\n"
                "  --verbose       Emit per-line execution metadata (JSON to stderr)\n"
                "  --version       Print version and exit\n"
                "  --help, -h      Show this help and exit\n"
                "\n"
                "With no file argument, starts an interactive REPL.\n"
                "Documentation: https://liminate.dev"
            )
            return 0
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
        had_error = run_file(
            positional[0],
            auto_confirm_amber=auto,
            quiet=quiet,
            verbose=verbose,
            domain_packs=domain_packs or None,
        )
        return 1 if had_error else 0
    else:
        repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

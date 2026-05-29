"""Public whole-program entry point for Liminate.

`run(source, ...)` is the single program-execution loop shared by the CLI
(`cli.run_file`) and external embedders (e.g. liminate-receipts). It takes
contract **text** and returns a structured `ContractResult`. It performs
**no I/O** — no `print`, no `input`, no file reads, no stdout/stderr.

Where `cli.run_file` previously owned the loop directly, it now reads the
file and delegates here. Display stays in `cli.display_result` (untouched);
this module surfaces each result through an injected `on_result` sink so the
CLI can render inline (preserving the exact ordering of amber confirmation
and quiet-mode blank-line mirroring) while embedders simply collect results.

Sources for the loop logic (relocated verbatim from `cli.run_file` /
`cli._consume_when_block`):
- v1c §48 (blank/comment lines skipped)
- v3a §107 (two-phase gate), §108/§110 (when-block buffering),
  §122 (listener result stream)
- Meta-Structural Era (the `about` declaration: first-eligible-line rule)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from .adapter import DomainPack, LiveValueRegistry
from .analyzer import SymbolEntry
from .interpreter import HandlerTable, execute
from .lexer import LexError, leading_indent, tokenize
from .listener import listen
from .parser import _ParseError, parse, parse_about, parse_when_block
from .reorderer import reorder
from .result import LiminateResult, ResultStatus
from .vocabulary import (
    TokenType,
    activate_pack_words,
    deactivate_all_pack_words,
)


# ---------------------------------------------------------------------------
# Session: the shared symbol table across statements (+ v3a listener state)
# ---------------------------------------------------------------------------
#
# `Session` is pure execution state (symbol table, handler table, live-value
# registry, pack wiring) — it belongs with the loop, not the CLI. It lives
# here and is re-exported by `cli` for the REPL and tests (v11 §22 invariant
# 3: dependency points cli → run, never run → cli).


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
        # Exit-code accumulator: tracks ALL error statuses across both
        # phases (parse, semantic, runtime), not just the Phase 1 gate
        # errors. run() returns this so callers can propagate a
        # non-zero exit code to automated consumers (CI, git hooks,
        # &&-chained commands). Errors are sticky — once set, stays set.
        self.had_any_error: bool = False
        # U1/U2 — display state for HANDLER_FIRE outputs. Tracks the
        # most recently-displayed trigger key so the [trigger-tag] prefix
        # appears once per firing rather than once per action statement.
        # Reset by display_result whenever a non-HANDLER_FIRE result is
        # surfaced (so any Phase-1 / shutdown / error line clears it).
        self._last_trigger_key: tuple | None = None

        # Meta-Structural Era: the `about` declaration's topic, set by
        # run() when the program's first eligible line is an `about`
        # declaration. Inert metadata — not stored in the symbol table.
        self.topic: str | None = None

        # v4a §137: pack vocabulary (verbs + nouns) is process-global
        # state. Reset before activating this Session's packs so the
        # active vocabulary always reflects the current Session, not a
        # leftover from an earlier one.
        deactivate_all_pack_words()
        for pack in self.domain_packs:
            verbs = pack.verbs()
            nouns = [w for (w, cat) in pack.vocabulary() if cat == "noun"]
            if verbs or nouns:
                activate_pack_words(
                    verbs=verbs, nouns=nouns, pack_name=pack.name(),
                )

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

    def run_line(self, line: str) -> LiminateResult | None:
        """Execute one source line. Returns the result, or None for blank."""
        try:
            tokens = tokenize(line)
        except LexError as e:
            # v2c §86/§92 — unclosed or empty quoted strings surface as
            # ERROR_PARSE (Outcome 4 per v1c §50).
            return LiminateResult(
                status=ResultStatus.ERROR_PARSE,
                message=e.message,
                executed=False,
            )
        if not tokens:
            return None
        reordered = reorder(tokens)
        if isinstance(reordered, LiminateResult):
            return reordered
        ast = parse(reordered, composition_names=self.composition_names())
        if isinstance(ast, LiminateResult):
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
    ) -> LiminateResult | None:
        """Execute a v3a `when` block — header line plus its already-
        de-indented action lines.

        The caller (run) is responsible for indentation validation
        (§110): tabs, deeper-than-block, empty block. By the time we
        get here, `action_lines` is a list of action statement strings
        with leading whitespace stripped — they tokenize and parse like
        any other line.
        """
        try:
            header_tokens = tokenize(header_line)
        except LexError as e:
            return LiminateResult(
                status=ResultStatus.ERROR_PARSE,
                message=e.message,
                executed=False,
            )
        header_reordered = reorder(header_tokens)
        if isinstance(header_reordered, LiminateResult):
            return header_reordered

        action_token_lists: list = []
        for raw in action_lines:
            try:
                toks = tokenize(raw)
            except LexError as e:
                return LiminateResult(
                    status=ResultStatus.ERROR_PARSE,
                    message=e.message,
                    executed=False,
                )
            if not toks:
                continue  # blank line inside the block — v1c §48
            re_ordered = reorder(toks)
            if isinstance(re_ordered, LiminateResult):
                return re_ordered
            action_token_lists.append(re_ordered)

        ast = parse_when_block(
            header_reordered, action_token_lists,
            composition_names=self.composition_names(),
        )
        if isinstance(ast, LiminateResult):
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

    def record_result(self, result: LiminateResult | None) -> None:
        """Track whether Phase 1 had any blocking outcomes (v3a §107).

        Called by the loop's emit funnel after each result so the Session
        can decide whether to enter Phase 2 once the source is exhausted.
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
        if result.status in (
            ResultStatus.ERROR_PARSE,
            ResultStatus.ERROR_SEMANTIC,
            ResultStatus.ERROR_RUNTIME,
        ):
            self.had_any_error = True


# ---------------------------------------------------------------------------
# ContractResult — the structured return type
# ---------------------------------------------------------------------------


@dataclass
class ContractResult:
    """Everything a non-CLI caller needs from a whole-program run.

    Mirrors the field set liminate-receipts already produces so PR 2 is a
    drop-in. `run()` returns `LiminateResult` objects (not serialized
    dicts) — serialization is each caller's concern (the CLI renders to
    stdout; Receipts serializes to JSON).
    """
    results: list[LiminateResult]
    symbol_table: dict[str, SymbolEntry]
    topic: str | None = None
    had_error: bool = False


# Internal `emit` funnel contract (used by `_consume_when_block`): a callable
# `emit(result, line_num, timestamp, duration_ms)` invoked once per produced
# result in execution order. `line_num` is the 1-based source line for
# Phase-1 results, or None for Phase-2 (listener) results.
# `timestamp`/`duration_ms` mirror the values `cli.run_file` previously fed
# `_emit_verbose_metadata`.
EmitSink = Callable[[LiminateResult | None, int | None, str | None, float | None], None]

# External per-result sink supplied by callers via `run(..., on_result=)`.
# Receives the live `Session` so a display sink can render against the same
# symbol table / trigger state the loop is mutating (the CLI passes a
# closure over `display_result`).
ResultSink = Callable[
    [LiminateResult | None, "Session", int | None, str | None, float | None],
    None,
]


# ---------------------------------------------------------------------------
# when-block buffering (v3a §110) — the single copy of the indentation logic
# ---------------------------------------------------------------------------


def _buffer_when_block(
    lines: list[str],
    start_idx: int,
    *,
    on_blank: Callable[[], None] | None = None,
) -> tuple[str, list[str], str | None, int]:
    """Buffer the indented action block starting at line `start_idx + 1`.

    Returns `(header_line, action_lines, block_error, next_index)`:
    - `action_lines` are the de-indented action statement strings.
    - `block_error` is a §110 indentation error message, or None.
    - `next_index` is the first line index the caller should resume at
      (one past the bad line on error; the first un-consumed line on
      success — matching the historic `consumed_through + 1` / `j`).

    `on_blank()` is invoked for each blank/comment line skipped inside the
    block — the CLI uses it for quiet-mode blank-line mirroring. This is
    the only behavioral coupling to display, and it is injected, not done
    here (this function performs no I/O of its own).
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
        # Comment lines (`--` prefix) are treated the same way — they do
        # not establish or violate the block's indentation depth.
        next_stripped = next_line.lstrip()
        if not next_stripped or next_stripped.startswith("--"):
            if on_blank is not None:
                on_blank()
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

    next_index = (consumed_through + 1) if block_error is not None else j
    return header_line, action_lines, block_error, next_index


def _consume_when_block(
    lines: list[str],
    start_idx: int,
    session: Session,
    *,
    emit: EmitSink,
    on_blank: Callable[[], None] | None = None,
) -> int:
    """Buffer + execute the `when` block starting at `start_idx`, funnelling
    the produced result through `emit`. Returns the next index to process.

    Stamps `timestamp`/`duration_ms` on the executed result exactly where
    `cli._consume_when_block` historically did (success path only); error
    results carry no object stamp but `emit` still receives `(ts, 0.0)` so
    verbose metadata is byte-identical.
    """
    header_line, action_lines, block_error, next_index = _buffer_when_block(
        lines, start_idx, on_blank=on_blank,
    )

    if block_error is not None:
        err = LiminateResult(
            status=ResultStatus.ERROR_PARSE,
            message=block_error,
            executed=False,
        )
        ts = datetime.now(timezone.utc).isoformat()
        err.line = start_idx + 1
        err.source = header_line
        err.timestamp = ts
        err.duration_ms = 0.0
        emit(err, start_idx + 1, ts, 0.0)
        return next_index

    ts = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    result = session.run_when_block(header_line, action_lines)
    dur = round((time.monotonic() - t0) * 1000, 3)
    if result is not None:
        result.timestamp = ts
        result.duration_ms = dur
        result.line = start_idx + 1
        result.source = header_line
    emit(result, start_idx + 1, ts, dur)
    return next_index


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run(
    source: str,
    *,
    domain_packs: list[DomainPack] | None = None,
    auto_confirm_amber: bool = False,
    enter_phase2: bool = True,
    on_result: ResultSink | None = None,
    on_blank: Callable[[], None] | None = None,
) -> ContractResult:
    """Execute a Liminate program from source text and return structured
    results. Performs NO I/O — no print, no input, no file reads, no
    stdout. The single program-execution entry point shared by the CLI
    and Receipts.

    Parameters:
    - `source`: contract text (not a path — file reading is the caller's).
    - `domain_packs`: already-loaded packs (pack *loading* from a path/JSON
      arg stays in `cli.load_pack_from_arg`).
    - `auto_confirm_amber`: when no `on_result` sink is supplied (embedder
      mode), amber outcomes are resolved by executing the pending AST —
      mirroring the historic `--test` / runner `_confirm_amber` behavior —
      with no `input()` call. When False, amber results are left in
      `results` unresolved for the caller to handle.
    - `enter_phase2`: when True (default — the CLI's behavior), the
      event-driven listener runs after Phase 1 if any `when` handler
      registered and Phase 1 had no errors. When False, Phase 2 is skipped
      entirely: handlers are still registered during Phase 1 (so the
      registration result appears in `results`) but never fire, and no
      LISTENING/HANDLER_FIRE/SHUTDOWN results are produced. Static
      inspectors (e.g. Receipts) that treat a contract as text — not a live
      reactive program — pass `enter_phase2=False`.
    - `on_result`: optional per-result sink (the CLI passes a closure that
      calls `display_result`). When supplied, amber confirmation and
      blank-line rendering are the sink's responsibility (it runs inline at
      the exact loop position, preserving ordering); `run` does not resolve
      amber itself in that case.
    - `on_blank`: optional callback invoked for each blank/comment line
      skipped at top level (CLI uses it for quiet-mode blank mirroring).

    Each produced `LiminateResult` carries `line` (1-based source line) and
    `source` (raw line text) so embedders can serialize per-line without
    re-running the loop.
    """
    session = Session(domain_packs=domain_packs)
    results: list[LiminateResult] = []

    amber_statuses = (
        ResultStatus.AMBER_PRECEDENCE,
        ResultStatus.AMBER_AMBIGUITY,
    )

    def _emit(
        result: LiminateResult | None,
        line_num: int | None,
        ts: str | None,
        dur: float | None,
    ) -> None:
        """Single funnel for every produced result (Phase 1 + Phase 2)."""
        # Embedder mode (no display sink): resolve amber non-interactively so
        # the returned `results` reflect confirmation, *replacing* the amber
        # result with its executed form — matching the historic runner
        # `_confirm_amber` semantics (one result per line, not two). The
        # source-position/timing metadata carries onto the resolved result.
        # With a display sink, the sink (display_result) resolves amber inline
        # instead — resolving here too would double-execute the pending AST.
        if (
            on_result is None
            and auto_confirm_amber
            and result is not None
            and result.status in amber_statuses
            and result.pending_ast is not None
        ):
            resolved = execute(result.pending_ast, session.symtab)
            resolved.line = result.line
            resolved.source = result.source
            resolved.timestamp = result.timestamp
            resolved.duration_ms = result.duration_ms
            result = resolved
        if result is not None:
            results.append(result)
        if on_result is not None:
            on_result(result, session, line_num, ts, dur)
        session.record_result(result)

    lines = source.splitlines()

    # Meta-Structural Era: track whether the first eligible (non-blank,
    # non-comment) line has been seen, so `about` is recognized only as
    # the first line and a second `about` anywhere is rejected (MS-Q1).
    first_eligible_seen = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # v1c §48 — blank lines are skipped by the lexer. --quiet mirrors
        # them so the user's paragraph breaks survive (U1/U4). Comment
        # lines (`--` after optional leading whitespace) are handled
        # identically: the lexer returns [] for both.
        stripped = line.lstrip()
        if not stripped or stripped.startswith("--"):
            if on_blank is not None:
                on_blank()
            i += 1
            continue

        # Meta-Structural Era: an `about` declaration is consumed before
        # the normal pipeline. It must be the first eligible line and may
        # appear at most once. A `DECLARATION` token anywhere else (a
        # second `about`, or `about` after a normal statement) is an
        # ERROR_PARSE.
        try:
            decl_tokens = tokenize(line)
        except LexError:
            decl_tokens = []
        if decl_tokens and decl_tokens[0].type is TokenType.DECLARATION:
            if first_eligible_seen or session.topic is not None:
                err = LiminateResult(
                    status=ResultStatus.ERROR_PARSE,
                    message=(
                        "'about' is a declaration that must be the first "
                        "line of the program (after any comments). Only one "
                        "'about' declaration is allowed."
                    ),
                    executed=False,
                )
            else:
                try:
                    node = parse_about(decl_tokens)
                    session.topic = node.topic
                    err = None
                except _ParseError as e:
                    err = LiminateResult(
                        status=ResultStatus.ERROR_PARSE,
                        message=e.message,
                        executed=False,
                    )
            first_eligible_seen = True
            if err is not None:
                ts = datetime.now(timezone.utc).isoformat()
                err.line = i + 1
                err.source = line
                err.timestamp = ts
                err.duration_ms = 0.0
                _emit(err, i + 1, ts, 0.0)
            i += 1
            continue
        first_eligible_seen = True

        # Tab-in-leading-whitespace is a v3a §110 lex error — surface it
        # as ERROR_PARSE and skip this line.
        try:
            indent = leading_indent(line)
        except LexError as e:
            err = LiminateResult(
                status=ResultStatus.ERROR_PARSE,
                message=e.message,
                executed=False,
            )
            ts = datetime.now(timezone.utc).isoformat()
            err.line = i + 1
            err.source = line
            err.timestamp = ts
            err.duration_ms = 0.0
            _emit(err, i + 1, ts, 0.0)
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
                emit=_emit,
                on_blank=on_blank,
            )
            continue

        # Regular Phase 1 sequential statement.
        ts = datetime.now(timezone.utc).isoformat()
        t0 = time.monotonic()
        result = session.run_line(line)
        dur = round((time.monotonic() - t0) * 1000, 3)
        if result is not None:
            result.timestamp = ts
            result.duration_ms = dur
            result.line = i + 1
            result.source = line
        _emit(result, i + 1, ts, dur)
        i += 1

    # v3a §107 — Phase 2 gate: only enter listener mode if the caller opted
    # in (enter_phase2), Phase 1 had zero errors, AND at least one handler
    # registered. Otherwise the source executed as a regular v2d program (or
    # the caller — e.g. a static inspector — asked to stop after Phase 1).
    if (
        not enter_phase2
        or session.handler_table.is_empty()
        or session.phase1_had_error
    ):
        return ContractResult(
            results=results,
            symbol_table=session.symtab,
            topic=session.topic,
            had_error=session.had_any_error,
        )

    # Phase 2 streams results from the listener generator. v3a §122 data
    # (HANDLER_FIRE output, SHUTDOWN message, errors) carries no per-line
    # source position, so listener results are emitted with line_num=None
    # (and never feed verbose metadata — matching the historic loop).
    adapters = session.adapters()
    for result in listen(
        session.symtab,
        session.handler_table,
        session.live_value_registry,
        adapters,
    ):
        _emit(result, None, None, None)

    return ContractResult(
        results=results,
        symbol_table=session.symtab,
        topic=session.topic,
        had_error=session.had_any_error,
    )

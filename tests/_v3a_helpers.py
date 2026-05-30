"""Shared test infrastructure for v3a (Phase 1 + Phase 2) integration tests.

The leading underscore signals "test infra, not a test module pytest
should collect." Two test files use these helpers:
  - tests/test_integration_v3a.py (sentence-level v3a coverage)
  - tests/test_timer_pack.py (timer domain pack end-to-end)
"""

from __future__ import annotations

import textwrap

from liminate.adapter import DomainPack
from liminate.cli import Session
from liminate.lexer import leading_indent, LexError, tokenize
from liminate.listener import listen
from liminate.result import LiminateResult, ResultStatus
from liminate.vocabulary import TokenType


# ---------------------------------------------------------------------------
# In-memory run helper — mirrors cli.run_file but yields structured
# results instead of writing to stdout. Phase 1 + Phase 2 in one call.
# ---------------------------------------------------------------------------


def run_v3a(
    source: str,
    *,
    pack: DomainPack | None = None,
) -> tuple[Session, list[LiminateResult]]:
    """Run a v3a program through Phase 1 + (if any handlers register)
    Phase 2. Returns the Session and the full ordered list of yielded
    LiminateResult objects.

    Source is a multi-line string. `textwrap.dedent` strips the common
    Python-source leading indentation before line iteration so action
    lines preserve their relative depth — `when` headers land at indent
    0 and `  show "x"` lands at indent 2.
    """
    source = textwrap.dedent(source).strip("\n")
    session = Session(domain_packs=[pack] if pack else None)
    results: list[LiminateResult] = []
    lines = source.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        try:
            indent = leading_indent(line)
        except LexError as e:
            err = LiminateResult(
                status=ResultStatus.ERROR_PARSE,
                message=e.message,
                executed=False,
            )
            results.append(err)
            session.record_result(err)
            i += 1
            continue

        # Detect `when` header at indent 0.
        is_when = False
        if indent == 0:
            try:
                toks = tokenize(line)
            except LexError:
                toks = []
            if toks and toks[0].type is TokenType.CONNECTIVE and toks[0].value == "when":
                is_when = True
            # v0.12.0 — `inherited when` header (mirrors run.py / build.py).
            elif (
                len(toks) > 1
                and toks[0].type is TokenType.OPERATOR
                and toks[0].value == "inherited"
                and toks[1].type is TokenType.CONNECTIVE
                and toks[1].value == "when"
            ):
                is_when = True

        if is_when:
            action_lines: list[str] = []
            block_depth: int | None = None
            j = i + 1
            block_error: str | None = None
            while j < len(lines):
                next_line = lines[j]
                if not next_line.strip():
                    j += 1
                    continue
                try:
                    next_indent = leading_indent(next_line)
                except LexError as e:
                    block_error = e.message
                    j += 1
                    break
                if next_indent == 0:
                    break
                if block_depth is None:
                    block_depth = next_indent
                elif next_indent > block_depth:
                    block_error = (
                        f"This line is indented {next_indent} spaces, "
                        f"deeper than the block depth {block_depth}."
                    )
                    j += 1
                    break
                elif next_indent < block_depth:
                    break
                action_lines.append(next_line.lstrip(" "))
                j += 1
            if block_error is not None:
                err = LiminateResult(
                    status=ResultStatus.ERROR_PARSE,
                    message=block_error,
                    executed=False,
                )
                results.append(err)
                session.record_result(err)
            else:
                r = session.run_when_block(line, action_lines)
                if r is not None:
                    results.append(r)
                session.record_result(r)
            i = j
            continue

        r = session.run_line(line)
        if r is not None:
            results.append(r)
        session.record_result(r)
        i += 1

    # Phase 2 gate (v3a §107).
    if session.handler_table.is_empty():
        return session, results
    if session.phase1_had_error:
        return session, results

    adapters = session.adapters()
    for r in listen(
        session.symtab,
        session.handler_table,
        session.live_value_registry,
        adapters,
    ):
        results.append(r)

    return session, results


def fires(results: list[LiminateResult]) -> list[LiminateResult]:
    return [r for r in results if r.status is ResultStatus.HANDLER_FIRE]


def outputs(results: list[LiminateResult]) -> list[str]:
    """Flatten all data output across SUCCESS / HANDLER_FIRE results."""
    lines: list[str] = []
    for r in results:
        if r.status in (ResultStatus.SUCCESS, ResultStatus.HANDLER_FIRE) and r.output:
            lines.extend(r.output)
    return lines

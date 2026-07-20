"""Tests for the Z3 satisfiability checker (src/liminate/checker.py).

Decidability Step 2 — encodes Liminate's enforcement fragment (require/
forbid/permit/expect + define predicates) into SMT constraints and runs
seven authoring-time checks. See src/liminate/checker.py for the design
notes; this file mirrors its phase structure.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from liminate.cli import Session
from liminate.lexer import tokenize
from liminate.parser import parse
from liminate.analyzer import SymbolEntry
from liminate.reorderer import reorder
from liminate.result import LiminateResult


def _parse_line(line, predicate_names=None):
    reordered = reorder(tokenize(line))
    assert not isinstance(reordered, LiminateResult), line
    ast = parse(reordered, predicate_names=predicate_names)
    assert not isinstance(ast, LiminateResult), line
    return ast


def _condition_of(line, predicate_names=None):
    """Parse a require/forbid/permit/expect/define line and return the
    condition AST (the `.condition` field for deontic verbs)."""
    return _parse_line(line, predicate_names=predicate_names).condition


def run_lines(lines):
    session = Session()
    results = [session.run_line(line) for line in lines]
    return session, results


# ---------------------------------------------------------------------------
# Phase 1 — packaging: lazy z3 import
# ---------------------------------------------------------------------------


def test_checker_module_importable_without_z3():
    """`import liminate.checker` must succeed even when z3 cannot be
    imported at all — the module must not import z3 at top level."""
    script = (
        "import sys, builtins\n"
        "_orig_import = builtins.__import__\n"
        "def _blocked(name, *a, **k):\n"
        "    if name == 'z3' or name.startswith('z3.'):\n"
        "        raise ImportError('z3 not installed (simulated)')\n"
        "    return _orig_import(name, *a, **k)\n"
        "builtins.__import__ = _blocked\n"
        "import liminate.checker\n"
        "print('IMPORT_OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "IMPORT_OK" in result.stdout


def test_check_agreement_raises_checker_unavailable_without_z3():
    """Calling the public entry point without z3 installed raises
    CheckerUnavailable, not an ImportError or traceback."""
    script = (
        "import sys, builtins\n"
        "_orig_import = builtins.__import__\n"
        "def _blocked(name, *a, **k):\n"
        "    if name == 'z3' or name.startswith('z3.'):\n"
        "        raise ImportError('z3 not installed (simulated)')\n"
        "    return _orig_import(name, *a, **k)\n"
        "builtins.__import__ = _blocked\n"
        "import liminate.checker as checker\n"
        "try:\n"
        "    checker.check_agreement([], {})\n"
        "except checker.CheckerUnavailable as e:\n"
        "    print('RAISED_CHECKER_UNAVAILABLE')\n"
        "    print(str(e))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "RAISED_CHECKER_UNAVAILABLE" in result.stdout
    assert "pip install liminate[check]" in result.stdout


# ---------------------------------------------------------------------------
# Phase 2 — sort model and constant allocation
# ---------------------------------------------------------------------------

z3 = pytest.importorskip("z3")

from liminate import checker  # noqa: E402  (after importorskip)


def test_constant_map_number_string_date_record_and_string_list():
    symtab = {
        "amount": SymbolEntry(name="amount", value=10, type="number"),
        "status": SymbolEntry(name="status", value="open", type="string"),
        "due": SymbolEntry(
            name="due", value=__import__("datetime").date(2026, 1, 1), type="date"
        ),
        "order1": SymbolEntry(
            name="order1",
            value={"total": 50, "label": "x"},
            type="record",
            schema={"total": "number", "label": "string"},
        ),
        "tags": SymbolEntry(
            name="tags", value=["a", "b"], type="list_of_strings"
        ),
    }
    enc = checker._Encoder(z3, symtab, {})

    assert enc.constants["amount"].sort() == z3.RealSort()
    assert enc.constants["status"].sort() == z3.StringSort()
    assert enc.constants["due"].sort() == z3.IntSort()
    assert enc.constants["order1__total"].sort() == z3.RealSort()
    assert enc.constants["order1__label"].sort() == z3.StringSort()

    # No constant is allocated for a list — membership expands to a
    # disjunction at encode time instead.
    assert "tags" not in enc.constants

    # Reverse map round-trips for every allocated constant.
    for original in ("amount", "status", "due", "order1__total", "order1__label"):
        sanitized = enc._sanitize(original)
        assert enc.reverse[sanitized] == original


def test_constant_map_sanitizes_hyphenated_names():
    symtab = {
        "actor-teams": SymbolEntry(name="actor-teams", value=1, type="number"),
    }
    enc = checker._Encoder(z3, symtab, {})
    const = enc.constants["actor-teams"]
    # Must be a legal Z3/SMT identifier — no raw hyphen survives.
    assert "-" not in str(const)
    assert enc.reverse[enc._sanitize("actor-teams")] == "actor-teams"


def test_date_ordinal_helper_matches_toordinal():
    import datetime

    d = datetime.date(2026, 7, 20)
    assert checker._date_ordinal(d) == d.toordinal()

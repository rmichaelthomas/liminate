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


# ---------------------------------------------------------------------------
# Phase 3 — condition encoder
# ---------------------------------------------------------------------------


def _pinned(enc, name, value):
    """A solver assumption pinning a free constant to a concrete value,
    so a structurally-free condition formula gets a definite sat/unsat
    verdict for a specific fact assignment."""
    return enc.constants[name] == value


def _check_with(formula, *assumptions):
    s = z3.Solver()
    for a in assumptions:
        s.add(a)
    s.add(formula)
    return s.check()


def _number_symtab(**facts):
    return {name: SymbolEntry(name=name, value=v, type="number") for name, v in facts.items()}


def test_op_is_and_equal_to():
    for line in ("require amount is 50", "require amount is equal to 50"):
        enc = checker._Encoder(z3, _number_symtab(amount=0), {})
        formula = enc.encode_condition(_condition_of(line))
        assert _check_with(formula, _pinned(enc, "amount", 50)) == z3.sat
        assert _check_with(formula, _pinned(enc, "amount", 51)) == z3.unsat


def test_op_not_equal_to():
    enc = checker._Encoder(z3, _number_symtab(amount=0), {})
    formula = enc.encode_condition(_parse_line("require amount is not equal to 50").condition)
    assert _check_with(formula, _pinned(enc, "amount", 51)) == z3.sat
    assert _check_with(formula, _pinned(enc, "amount", 50)) == z3.unsat


def test_op_above():
    enc = checker._Encoder(z3, _number_symtab(amount=0), {})
    formula = enc.encode_condition(_condition_of("require amount is above 50"))
    assert _check_with(formula, _pinned(enc, "amount", 60)) == z3.sat
    assert _check_with(formula, _pinned(enc, "amount", 40)) == z3.unsat


def test_op_below():
    enc = checker._Encoder(z3, _number_symtab(amount=0), {})
    formula = enc.encode_condition(_condition_of("require amount is below 50"))
    assert _check_with(formula, _pinned(enc, "amount", 40)) == z3.sat
    assert _check_with(formula, _pinned(enc, "amount", 60)) == z3.unsat


def test_op_not_above():
    """not_above is a fused <=, not a structural Not(above) wrapper."""
    enc = checker._Encoder(z3, _number_symtab(amount=0), {})
    formula = enc.encode_condition(_parse_line("require amount is not above 50").condition)
    assert _check_with(formula, _pinned(enc, "amount", 50)) == z3.sat  # boundary included
    assert _check_with(formula, _pinned(enc, "amount", 51)) == z3.unsat


def test_op_not_below():
    """not_below is a fused >=, not a structural Not(below) wrapper."""
    enc = checker._Encoder(z3, _number_symtab(amount=0), {})
    formula = enc.encode_condition(_parse_line("require amount is not below 50").condition)
    assert _check_with(formula, _pinned(enc, "amount", 50)) == z3.sat  # boundary included
    assert _check_with(formula, _pinned(enc, "amount", 49)) == z3.unsat


def test_op_within_operand_order_not_swapped():
    """§3 correction (1): value is tolerance, value2 is target. A swap
    would make amount=50 satisfiable; the correct encoding must not."""
    enc = checker._Encoder(z3, _number_symtab(amount=0), {})
    cond = _parse_line("require amount is within 5 of 100").condition
    formula = enc.encode_condition(cond)
    assert _check_with(formula, _pinned(enc, "amount", 100)) == z3.sat
    assert _check_with(formula, _pinned(enc, "amount", 105)) == z3.sat   # boundary
    assert _check_with(formula, _pinned(enc, "amount", 106)) == z3.unsat
    assert _check_with(formula, _pinned(enc, "amount", 50)) == z3.unsat  # would be sat if swapped


def test_op_includes_present_value_is_satisfiable():
    symtab = {
        "tags": SymbolEntry(name="tags", value=["urgent", "normal"], type="list_of_strings"),
    }
    enc = checker._Encoder(z3, symtab, {})
    cond = _parse_line('require tags includes "urgent"').condition
    formula = enc.encode_condition(cond)
    assert _check_with(formula) == z3.sat


def test_op_includes_absent_value_is_unsatisfiable():
    symtab = {
        "tags": SymbolEntry(name="tags", value=["urgent", "normal"], type="list_of_strings"),
    }
    enc = checker._Encoder(z3, symtab, {})
    cond = _parse_line('require tags includes "missing"').condition
    formula = enc.encode_condition(cond)
    assert _check_with(formula) == z3.unsat


def test_op_not_includes_mirrors_includes():
    symtab = {
        "tags": SymbolEntry(name="tags", value=["urgent", "normal"], type="list_of_strings"),
    }
    enc = checker._Encoder(z3, symtab, {})
    present = _parse_line('require tags not includes "urgent"').condition
    absent = _parse_line('require tags not includes "missing"').condition
    assert _check_with(enc.encode_condition(present)) == z3.unsat
    assert _check_with(enc.encode_condition(absent)) == z3.sat


def test_op_includes_empty_list_special_case():
    symtab = {
        "tags": SymbolEntry(name="tags", value=[], type="list_of_strings"),
    }
    enc = checker._Encoder(z3, symtab, {})
    includes_cond = _parse_line('require tags includes "x"').condition
    not_includes_cond = _parse_line('require tags not includes "x"').condition
    assert _check_with(enc.encode_condition(includes_cond)) == z3.unsat
    assert _check_with(enc.encode_condition(not_includes_cond)) == z3.sat


def test_compound_and_or():
    enc = checker._Encoder(z3, _number_symtab(amount=0), {})
    and_cond = _parse_line("require amount is above 10 and amount is below 20").condition
    or_cond = _parse_line("require amount is above 100 or amount is below 5").condition
    and_formula = enc.encode_condition(and_cond)
    or_formula = enc.encode_condition(or_cond)
    assert _check_with(and_formula, _pinned(enc, "amount", 15)) == z3.sat
    assert _check_with(and_formula, _pinned(enc, "amount", 30)) == z3.unsat
    assert _check_with(or_formula, _pinned(enc, "amount", 200)) == z3.sat
    assert _check_with(or_formula, _pinned(enc, "amount", 50)) == z3.unsat


def test_predicate_application_substitutes_each_pronoun_and_resolves_outer_symbols():
    """§3 corrections (2) and (3): the predicate body's implicit field
    binds to EachPronoun, substituted with the application's subject;
    every other name in the body (cutoff) resolves normally."""
    session, results = run_lines([
        "remember a number called cutoff with 100",
        "define big: is above cutoff",
    ])
    for r in results:
        assert r.status.name == "SUCCESS", r.message
    symtab = dict(session.symtab)
    symtab["amount"] = SymbolEntry(name="amount", value=0, type="number")
    enc = checker._Encoder(z3, symtab, {})
    cond = _condition_of("forbid amount is big", predicate_names={"big"})
    formula = enc.encode_condition(cond)
    cutoff = _pinned(enc, "cutoff", 100)
    assert _check_with(formula, cutoff, _pinned(enc, "amount", 150)) == z3.sat
    assert _check_with(formula, cutoff, _pinned(enc, "amount", 50)) == z3.unsat


def test_predicate_application_negated():
    session, results = run_lines([
        "remember a number called cutoff with 100",
        "define big: is above cutoff",
    ])
    for r in results:
        assert r.status.name == "SUCCESS", r.message
    symtab = dict(session.symtab)
    symtab["amount"] = SymbolEntry(name="amount", value=0, type="number")
    enc = checker._Encoder(z3, symtab, {})
    cond = _condition_of("forbid amount is not big", predicate_names={"big"})
    formula = enc.encode_condition(cond)
    cutoff = _pinned(enc, "cutoff", 100)
    assert _check_with(formula, cutoff, _pinned(enc, "amount", 150)) == z3.unsat
    assert _check_with(formula, cutoff, _pinned(enc, "amount", 50)) == z3.sat


def test_predicate_application_missing_definition_is_unencodable():
    symtab = _number_symtab(amount=0)
    enc = checker._Encoder(z3, symtab, {})
    cond = checker.PredicateApplicationNode(
        subject=checker.NameRef(name="amount"), predicate_name="ghost", negated=False,
    )
    with pytest.raises(checker.UnencodableConstruct):
        enc.encode_condition(cond)


def test_predicate_depth_guard_on_hand_built_cycle():
    """Belt-and-braces defense (§6) mirroring interpreter's
    _MAX_PREDICATE_EVAL_DEPTH, exercised via a hand-built symbol table
    since the analyzer (PR #60/#61) already rejects real self-reference."""
    symtab = _number_symtab(amount=0)
    cyclic_body = checker.PredicateApplicationNode(
        subject=checker.EachPronoun(), predicate_name="loopy", negated=False,
    )
    symtab["loopy"] = SymbolEntry(name="loopy", value=cyclic_body, type="predicate")
    enc = checker._Encoder(z3, symtab, {})
    cond = checker.PredicateApplicationNode(
        subject=checker.NameRef(name="amount"), predicate_name="loopy", negated=False,
    )
    with pytest.raises(checker.UnencodableConstruct):
        enc.encode_condition(cond)


def test_extrema_and_top_level_each_pronoun_are_unencodable():
    symtab = _number_symtab(amount=0, cap=0)
    enc = checker._Encoder(z3, symtab, {})
    with pytest.raises(checker.UnencodableConstruct):
        enc.encode_field(checker.EachPronoun())
    with pytest.raises(checker.UnencodableConstruct):
        enc.encode_value(checker.EachPronoun())


# ---------------------------------------------------------------------------
# Phase 4 — arithmetic, name inlining, TI-Q13 closure
# ---------------------------------------------------------------------------


def test_build_definitions_from_remember_value_nodes():
    statements = [_parse_line(l) for l in [
        "remember a number called beta with 4",
        "remember a number called z from beta multiplied by beta",
        "forbid alpha is above z",
    ]]
    definitions = checker._build_definitions(statements)
    assert set(definitions) == {"beta", "z"}
    assert isinstance(definitions["z"], checker.ArithmeticNode)


def test_build_definitions_later_overwrites_earlier():
    statements = [_parse_line(l) for l in [
        "remember a number called w with 1",
        "remember a number called w with 2",
    ]]
    definitions = checker._build_definitions(statements)
    assert isinstance(definitions["w"], checker.NumberLiteral)
    assert definitions["w"].value == 2


def test_build_definitions_descends_into_sequence_node():
    seq = checker.SequenceNode(
        operations=[
            _parse_line("remember a number called w with 1"),
            _parse_line("remember a number called v with 2"),
        ],
        connectors=["and"],
    )
    definitions = checker._build_definitions([seq])
    assert set(definitions) == {"w", "v"}


def test_inlining_applies_when_defining_expression_has_arithmetic():
    definitions = {
        "beta": checker.NumberLiteral(value=4),
        "z": checker.ArithmeticNode(
            left=checker.BareWord(word="beta"),
            right=checker.BareWord(word="beta"),
            op="multiplied_by",
        ),
    }
    symtab = _number_symtab(beta=4, alpha=0)
    enc = checker._Encoder(z3, symtab, definitions)
    with pytest.raises(checker.NonlinearArithmetic):
        enc.encode_value(checker.BareWord(word="z"))


def test_inlining_skipped_when_defining_expression_has_no_arithmetic():
    """A plain `remember ... with 4` (no ArithmeticNode in its defining
    expression) is NOT inlined — it resolves to its opaque constant."""
    definitions = {"w": checker.NumberLiteral(value=4)}
    symtab = _number_symtab(w=4)
    enc = checker._Encoder(z3, symtab, definitions)
    result = enc.encode_value(checker.BareWord(word="w"))
    assert result is enc.constants["w"]


def test_self_reference_guard_falls_back_to_opaque_constant():
    """`remember a number called x from x plus 1` — inlining must not
    recurse infinitely; on revisit it falls back to the opaque constant."""
    definitions = {
        "x": checker.ArithmeticNode(
            left=checker.BareWord(word="x"),
            right=checker.NumberLiteral(value=1),
            op="plus",
        ),
    }
    symtab = _number_symtab(x=0)
    enc = checker._Encoder(z3, symtab, definitions)
    result = enc.encode_value(checker.BareWord(word="x"))  # must not raise / hang
    assert result is not None


def test_multiplied_by_nonlinear_when_neither_operand_constant():
    definitions = {
        "beta": checker.NumberLiteral(value=4),
    }
    symtab = _number_symtab(beta=4)
    enc = checker._Encoder(z3, symtab, definitions)
    node = checker.ArithmeticNode(
        left=checker.BareWord(word="beta"),
        right=checker.BareWord(word="beta"),
        op="multiplied_by",
    )
    with pytest.raises(checker.NonlinearArithmetic):
        enc.encode_value(node)


def test_multiplied_by_linear_when_one_operand_is_a_literal():
    symtab = _number_symtab(beta=4)
    enc = checker._Encoder(z3, symtab, {})
    node = checker.ArithmeticNode(
        left=checker.BareWord(word="beta"),
        right=checker.NumberLiteral(value=2),
        op="multiplied_by",
    )
    result = enc.encode_value(node)  # must not raise
    assert result is not None


def test_divided_by_nonlinear_when_neither_operand_constant():
    symtab = _number_symtab(beta=4, gamma=2)
    enc = checker._Encoder(z3, symtab, {})
    node = checker.ArithmeticNode(
        left=checker.BareWord(word="beta"),
        right=checker.BareWord(word="gamma"),
        op="divided_by",
    )
    with pytest.raises(checker.NonlinearArithmetic):
        enc.encode_value(node)


def test_TI_Q13_checker_rejects_value_indirection_the_analyzer_permits():
    """Matched pair with tests/test_arithmetic.py's
    test_KNOWN_GAP_value_indirection_bypasses_the_linearity_restriction,
    which deliberately pins that liminate.run()/the analyzer PASS this
    program: PR #62's syntactic linearity check sees only a bare
    NameRef/BareWord in the condition, never the ArithmeticNode that
    produced it. The checker closes that gap by inlining the value at
    encode time and rejecting the nonlinear multiplication it exposes."""
    lines = [
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "remember a value called doubled from beta multiplied by beta",
        "forbid alpha is above doubled",
    ]
    session, results = run_lines(lines)
    for r in results[:-1]:
        assert r.status.name == "SUCCESS", r.message
    assert results[-1].status.name == "PROHIBITION_VIOLATED"  # liminate.run() accepts + enforces it

    statements = [_parse_line(l) for l in lines]
    definitions = checker._build_definitions(statements)
    enc = checker._Encoder(z3, session.symtab, definitions)
    cond = statements[-1].condition
    with pytest.raises(checker.NonlinearArithmetic) as excinfo:
        enc.encode_condition(cond)
    assert "doubled" in str(excinfo.value)

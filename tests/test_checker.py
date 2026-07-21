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


# ---------------------------------------------------------------------------
# Phase 5 — deontic statement effect formulas
# ---------------------------------------------------------------------------


def _pin_all(enc, symtab):
    """Pin every scalar fact the encoder allocated a constant for to its
    real interpreter value, so a formula referencing only those facts
    collapses to a concrete, closed boolean."""
    assumptions = []
    for name, entry in symtab.items():
        if name not in enc.constants:
            continue
        if entry.type == "date":
            assumptions.append(enc.constants[name] == checker._date_ordinal(entry.value))
        elif entry.type in ("number", "string"):
            assumptions.append(enc.constants[name] == entry.value)
    return assumptions


def _run_last_and_encode(lines):
    session, results = run_lines(lines)
    for r in results[:-1]:
        assert r.status.name == "SUCCESS", r.message
    last_ast = _parse_line(lines[-1])
    enc = checker._Encoder(z3, session.symtab, {})
    effect, allowed = enc.encode_deontic(last_ast)
    assumptions = _pin_all(enc, session.symtab)
    return results[-1], effect, allowed, assumptions


def test_require_effect_fires_iff_interpreter_halts():
    r, effect, _, assumptions = _run_last_and_encode([
        "remember a number called amount with 40",
        "require amount is above 50",
    ])
    assert r.status.name == "REQUIREMENT_NOT_MET"
    assert _check_with(effect, *assumptions) == z3.sat

    r2, effect2, _, assumptions2 = _run_last_and_encode([
        "remember a number called amount with 60",
        "require amount is above 50",
    ])
    assert r2.status.name == "SUCCESS"
    assert _check_with(effect2, *assumptions2) == z3.unsat


def test_require_unless_excuses_matches_interpreter():
    r, effect, _, assumptions = _run_last_and_encode([
        "remember a number called amount with 40",
        'remember a string called override with "yes"',
        "require amount is above 50 unless override is yes",
    ])
    assert r.status.name == "SUCCESS"  # excused
    assert _check_with(effect, *assumptions) == z3.unsat


def test_forbid_effect_fires_iff_interpreter_halts():
    r, effect, _, assumptions = _run_last_and_encode([
        "remember a number called amount with 60",
        "forbid amount is above 50",
    ])
    assert r.status.name == "PROHIBITION_VIOLATED"
    assert _check_with(effect, *assumptions) == z3.sat

    r2, effect2, _, assumptions2 = _run_last_and_encode([
        "remember a number called amount with 40",
        "forbid amount is above 50",
    ])
    assert r2.status.name == "SUCCESS"
    assert _check_with(effect2, *assumptions2) == z3.unsat


def test_forbid_unless_excuses_matches_interpreter():
    r, effect, _, assumptions = _run_last_and_encode([
        "remember a number called amount with 60",
        'remember a string called override with "yes"',
        "forbid amount is above 50 unless override is yes",
    ])
    assert r.status.name == "SUCCESS"  # excused
    assert _check_with(effect, *assumptions) == z3.unsat


def test_permit_effect_fires_iff_interpreter_emits():
    session, results = run_lines([
        "remember a number called amount with 60",
        "permit amount is above 50",
    ])
    assert results[-1].output is not None  # fired
    enc = checker._Encoder(z3, session.symtab, {})
    effect, allowed = enc.encode_deontic(_parse_line("permit amount is above 50"))
    assert allowed is None  # §8: permit never participates in allowed-space checks
    assumptions = _pin_all(enc, session.symtab)
    assert _check_with(effect, *assumptions) == z3.sat

    session2, results2 = run_lines([
        "remember a number called amount with 40",
        "permit amount is above 50",
    ])
    assert results2[-1].output is None  # did not fire
    enc2 = checker._Encoder(z3, session2.symtab, {})
    effect2, _ = enc2.encode_deontic(_parse_line("permit amount is above 50"))
    assumptions2 = _pin_all(enc2, session2.symtab)
    assert _check_with(effect2, *assumptions2) == z3.unsat


def test_expect_effect_fires_iff_interpreter_reports_divergence():
    session, results = run_lines([
        "remember a number called amount with 40",
        "expect amount is above 50",
    ])
    assert results[-1].output is not None  # divergence reported
    enc = checker._Encoder(z3, session.symtab, {})
    effect, allowed = enc.encode_deontic(_parse_line("expect amount is above 50"))
    assert allowed is None
    assumptions = _pin_all(enc, session.symtab)
    assert _check_with(effect, *assumptions) == z3.sat

    session2, results2 = run_lines([
        "remember a number called amount with 60",
        "expect amount is above 50",
    ])
    assert results2[-1].output is None  # met expectation, no report
    enc2 = checker._Encoder(z3, session2.symtab, {})
    effect2, _ = enc2.encode_deontic(_parse_line("expect amount is above 50"))
    assumptions2 = _pin_all(enc2, session2.symtab)
    assert _check_with(effect2, *assumptions2) == z3.unsat


def test_require_forbid_effect_and_allowed_are_logical_complements():
    for line in ("require amount is above 50", "forbid amount is above 50"):
        enc = checker._Encoder(z3, _number_symtab(amount=0), {})
        effect, allowed = enc.encode_deontic(_parse_line(line))
        s = z3.Solver()
        s.add(effect != enc.z3.Not(allowed))
        assert s.check() == z3.unsat  # no assignment breaks the complement


def test_exception_none_collapses_to_false():
    """When `exception` is None, E must behave as BoolVal(False) so the
    require/forbid formulas collapse to the unguarded shape."""
    enc = checker._Encoder(z3, _number_symtab(amount=0), {})
    node = _parse_line("require amount is above 50")
    assert node.exception is None
    effect, allowed = enc.encode_deontic(node)
    plain_condition = enc.encode_condition(node.condition)
    s = z3.Solver()
    s.add(allowed != plain_condition)
    assert s.check() == z3.unsat


# ---------------------------------------------------------------------------
# Phase 6 — the seven core checks
# ---------------------------------------------------------------------------


def _build_checker_context(lines, predicate_names=None):
    session, results = run_lines(lines)
    for r in results:
        assert r.status.name in (
            "SUCCESS", "REQUIREMENT_NOT_MET", "PROHIBITION_VIOLATED",
        ), r.message
    statements = [_parse_line(l, predicate_names=predicate_names) for l in lines]
    definitions = checker._build_definitions(statements)
    enc = checker._Encoder(z3, session.symtab, definitions)
    return enc, statements


def _findings_of_kind(findings, kind):
    return [f for f in findings if f.kind == kind]


def test_check1_always_deny_positive():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "require amount is above 50 and amount is below 10",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings = checker._check_always_deny(enc, entries)
    assert len(findings) == 1
    assert findings[0].severity == "error"


def test_check1_always_deny_negative():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "require amount is above 5",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings = checker._check_always_deny(enc, entries)
    assert findings == []


def test_check2_dead_forbid_positive():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "forbid amount is above 50 and amount is below 10",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings = checker._check_dead_forbid(enc, entries, swallowed=set())
    assert len(findings) == 1
    assert findings[0].severity == "warning"


def test_check2_dead_forbid_negative():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "forbid amount is above 50",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings = checker._check_dead_forbid(enc, entries, swallowed=set())
    assert findings == []


def test_check3_require_forbid_conflict_positive():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "require amount is above 100",
        "forbid amount is above 50",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings = checker._check_require_forbid_conflict(enc, entries, capped=False)
    assert len(findings) == 1
    assert findings[0].severity == "error"


def test_check3_require_forbid_conflict_negative():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "require amount is above 100",
        "forbid amount is above 200",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings = checker._check_require_forbid_conflict(enc, entries, capped=False)
    assert findings == []


def test_check3_skipped_when_capped():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "require amount is above 100",
        "forbid amount is above 50",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings = checker._check_require_forbid_conflict(enc, entries, capped=True)
    assert findings == []


def test_check4_unless_swallows_rule_positive_forbid():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "forbid amount is above 1000 unless amount is above 0",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings, swallowed = checker._check_unless_swallows_rule(enc, entries)
    assert len(findings) == 1
    assert findings[0].severity == "error"
    assert swallowed == {entries[0].index}


def test_check4_unless_swallows_rule_positive_require():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "require amount is above 5 unless amount is below 1000",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings, swallowed = checker._check_unless_swallows_rule(enc, entries)
    assert len(findings) == 1
    assert swallowed == {entries[0].index}


def test_check4_unless_swallows_rule_negative():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "forbid amount is above 1000 unless amount is above 2000",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings, swallowed = checker._check_unless_swallows_rule(enc, entries)
    assert findings == []
    assert swallowed == set()


def test_check4_suppresses_check2_for_same_statement():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "forbid amount is above 1000 unless amount is above 0",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    unless_findings, swallowed = checker._check_unless_swallows_rule(enc, entries)
    dead_forbid_findings = checker._check_dead_forbid(enc, entries, swallowed)
    assert _findings_of_kind(unless_findings, "unless_swallows_rule")
    assert dead_forbid_findings == []  # suppressed, not double-reported


def test_check5_redundant_forbid_positive():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "forbid amount is above 100",
        "forbid amount is above 50",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings = checker._check_redundant_forbid(enc, entries, capped=False)
    assert len(findings) == 1
    assert findings[0].severity == "warning"
    assert findings[0].statements[0] == entries[0].text  # the narrower one


def test_check5_redundant_forbid_negative():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        'remember a string called status with "open"',
        "forbid amount is above 50",
        'forbid status is equal to "blocked"',
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings = checker._check_redundant_forbid(enc, entries, capped=False)
    assert findings == []


def test_check5_skipped_when_capped():
    enc, statements = _build_checker_context([
        "remember a number called amount with 10",
        "forbid amount is above 100",
        "forbid amount is above 50",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings = checker._check_redundant_forbid(enc, entries, capped=True)
    assert findings == []


def test_check6_dead_permit_positive():
    enc, statements = _build_checker_context([
        "remember a number called amount with 5",
        "require amount is below 10",
        "permit amount is above 50",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings = checker._check_dead_permit(enc, entries)
    assert len(findings) == 1
    assert findings[0].severity == "warning"


def test_check6_dead_permit_negative():
    enc, statements = _build_checker_context([
        "remember a number called amount with 5",
        "require amount is below 100",
        "permit amount is above 50",
    ])
    entries = checker._collect_deontic_entries(enc, statements)
    findings = checker._check_dead_permit(enc, entries)
    assert findings == []


def test_check7_constant_predicate_contradiction():
    enc, statements = _build_checker_context([
        "define impossible: is above 100 and is below 50",
    ])
    findings = checker._check_constant_predicate(enc, statements)
    assert len(findings) == 1
    assert findings[0].severity == "warning"
    assert "never" in findings[0].explanation or "always false" in findings[0].explanation


def test_check7_constant_predicate_tautology():
    enc, statements = _build_checker_context([
        "define always_big_or_small: is above 0 or is below 1000000",
    ])
    findings = checker._check_constant_predicate(enc, statements)
    assert len(findings) == 1
    assert findings[0].severity == "warning"


def test_check7_constant_predicate_negative_resolves_outer_symbol():
    enc, statements = _build_checker_context([
        "remember a number called cutoff with 100",
        "define big: is above cutoff",
    ])
    findings = checker._check_constant_predicate(enc, statements)
    assert findings == []


def test_pairwise_cap_finding_helper():
    assert checker._cap_finding(200) is None
    finding = checker._cap_finding(201)
    assert finding is not None
    assert finding.severity == "info"
    assert finding.kind == "inconclusive"


def test_run_query_interprets_sat_unsat_unknown():
    enc, _ = _build_checker_context(["remember a number called amount with 5"])
    sat_status, _ = checker._run_query(enc, [(z3.BoolVal(True), "t")])
    assert sat_status == "sat"
    unsat_status, core = checker._run_query(enc, [(z3.BoolVal(False), "f")])
    assert unsat_status == "unsat"
    assert len(core) >= 1


def test_interpret_check_result_maps_unknown_to_inconclusive():
    assert checker._interpret_check_result(z3, z3.sat) == "sat"
    assert checker._interpret_check_result(z3, z3.unsat) == "unsat"
    assert checker._interpret_check_result(z3, z3.unknown) == "unknown"


def test_solver_timeout_configured_at_5000ms():
    assert checker._SOLVER_TIMEOUT_MS == 5000


# ---------------------------------------------------------------------------
# Phase 7 — public API (Finding / CheckResult / check_agreement)
# ---------------------------------------------------------------------------


def test_check_agreement_clean_program_zero_findings():
    lines = [
        "remember a number called amount with 60",
        "require amount is above 50",
        "forbid amount is above 1000",
    ]
    session, results = run_lines(lines)
    for r in results:
        assert r.status.name == "SUCCESS", r.message
    statements = [_parse_line(l) for l in lines]
    result = checker.check_agreement(statements, session.symtab)
    assert result.encodable is True
    assert result.findings == []
    assert result.checked == 2
    assert result.skipped_reason is None


def test_check_agreement_out_of_fragment_is_reported_not_crashed():
    node = checker.RequireNode(
        condition=checker.ConditionNode(
            field=checker.EachPronoun(), op="above", value=checker.NumberLiteral(value=5),
        ),
        exception=None,
    )
    result = checker.check_agreement([node], {})
    assert result.encodable is False
    assert result.skipped_reason is not None
    assert result.findings == []


def test_check_agreement_never_raises_for_malformed_symbol_table():
    result = checker.check_agreement([], None)
    assert result.encodable is False
    assert result.skipped_reason is not None


def test_check_agreement_ti_q13_integration_rejects_via_encodable_false():
    """The manual-gate pairing: liminate.run() accepts and enforces this
    program (see test_KNOWN_GAP_value_indirection_bypasses_the_linearity
    _restriction in tests/test_arithmetic.py); check_agreement rejects it."""
    lines = [
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "remember a value called doubled from beta multiplied by beta",
        "forbid alpha is above doubled",
    ]
    session, results = run_lines(lines)
    assert results[-1].status.name == "PROHIBITION_VIOLATED"
    statements = [_parse_line(l) for l in lines]
    result = checker.check_agreement(statements, session.symtab)
    assert result.encodable is False
    assert "doubled" in result.skipped_reason


def test_check_agreement_finds_unless_swallows_rule_end_to_end():
    lines = [
        "remember a number called amount with 10",
        "forbid amount is above 1000 unless amount is above 0",
    ]
    session, results = run_lines(lines)
    statements = [_parse_line(l) for l in lines]
    result = checker.check_agreement(statements, session.symtab)
    assert result.encodable is True
    kinds = [f.kind for f in result.findings]
    assert "unless_swallows_rule" in kinds
    assert "dead_forbid" not in kinds  # suppressed by check 4


def test_check_agreement_descends_into_sequence_node():
    seq = checker.SequenceNode(
        operations=[
            _parse_line("remember a number called amount with 10"),
            _parse_line("require amount is above 5 and amount is below 3"),
        ],
        connectors=["and"],
    )
    symtab = {"amount": SymbolEntry(name="amount", value=10, type="number")}
    result = checker.check_agreement([seq], symtab)
    assert result.encodable is True
    assert any(f.kind == "always_deny" for f in result.findings)


# ---------------------------------------------------------------------------
# Phase 8 — check_source: public export + text-in, CheckResult-out
# ---------------------------------------------------------------------------


def test_liminate_package_importable_without_z3():
    """`import liminate` must succeed even when z3 cannot be imported at
    all — mirrors test_checker_module_importable_without_z3 above, but for
    the package root now that it re-exports names from checker.py."""
    script = (
        "import sys, builtins\n"
        "_orig_import = builtins.__import__\n"
        "def _blocked(name, *a, **k):\n"
        "    if name == 'z3' or name.startswith('z3.'):\n"
        "        raise ImportError('z3 not installed (simulated)')\n"
        "    return _orig_import(name, *a, **k)\n"
        "builtins.__import__ = _blocked\n"
        "import liminate\n"
        "assert callable(liminate.check_agreement)\n"
        "assert callable(liminate.check_source)\n"
        "print('IMPORT_OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "IMPORT_OK" in result.stdout


def test_check_agreement_and_friends_exported_from_package():
    import liminate

    assert liminate.check_agreement is checker.check_agreement
    assert liminate.CheckResult is checker.CheckResult
    assert liminate.Finding is checker.Finding
    assert liminate.CheckerUnavailable is checker.CheckerUnavailable
    assert liminate.check_source is checker.check_source
    for name in (
        "CheckerUnavailable", "CheckResult", "Finding",
        "check_agreement", "check_source",
    ):
        assert name in liminate.__all__


def test_check_source_finds_unless_swallows_rule():
    source = "\n".join([
        "remember a number called amount with 10",
        "forbid amount is above 1000 unless amount is above 0",
    ])
    result = checker.check_source(source)
    assert isinstance(result, checker.CheckResult)
    assert result.encodable is True
    kinds = [f.kind for f in result.findings]
    assert "unless_swallows_rule" in kinds


def test_check_source_finds_constant_predicate_regression_for_define_node():
    """Regression test for the DefineNode trap: a naive collector built on
    run._collect_deontic_statements tracks `define` names into
    predicate_names but never appends the DefineNode itself, so check 7
    (_check_constant_predicate, which iterates DefineNode from the
    statement list) silently finds nothing. This program has zero
    require/forbid/permit/expect statements — checked stays 0 — but must
    still surface the constant_predicate finding for the tautological
    `define`."""
    source = "define always_big_or_small: is above 0 or is below 1000000"
    result = checker.check_source(source)
    assert isinstance(result, checker.CheckResult)
    assert result.encodable is True
    assert result.checked == 0
    kinds = [f.kind for f in result.findings]
    assert "constant_predicate" in kinds


def test_check_source_threads_predicate_names_matches_hand_built_ast():
    """Both require and forbid apply the named predicate `big` to the same
    field — proves check_source's collector threads predicate_names the
    same way a hand-built AST list (built exactly like the rest of this
    file's tests do, via _parse_line with predicate_names threaded by
    hand) would, rather than misparsing `is big` as string equality."""
    lines = [
        "remember a number called cutoff with 100",
        "define big: is above cutoff",
        "remember a number called amount with 150",
        "require amount is big",
        "forbid amount is big",
    ]
    source = "\n".join(lines)
    session, results = run_lines(lines)
    for r in results:
        assert r.status.name in ("SUCCESS", "PROHIBITION_VIOLATED"), r.message

    predicate_names = set()
    define_ast = _parse_line(lines[1], predicate_names=predicate_names)
    predicate_names.add(define_ast.name)
    hand_built = [
        define_ast,
        _parse_line(lines[3], predicate_names=predicate_names),
        _parse_line(lines[4], predicate_names=predicate_names),
    ]

    expected = checker.check_agreement(hand_built, session.symtab)
    actual = checker.check_source(source)

    assert actual.encodable == expected.encodable
    assert actual.checked == expected.checked
    assert [(f.kind, f.severity, f.statements) for f in actual.findings] == [
        (f.kind, f.severity, f.statements) for f in expected.findings
    ]
    assert [f.kind for f in actual.findings] == ["require_forbid_conflict"]


def test_check_source_out_of_fragment_nonlinear_via_remembered_name():
    """Doubles as the RememberValueNode-collection regression test: the
    nonlinearity in `doubled`'s definition (beta multiplied by beta, both
    runtime names) is only visible to check_agreement if the collector
    appended `doubled`'s RememberValueNode into the statement list for
    _build_definitions to find. A collector that only gathers deontic
    verbs (dropping value-form remember lines) would hand check_agreement
    a `doubled` that resolves to an opaque, already-allocated constant —
    missing the nonlinear multiplication entirely and reporting a clean
    (wrong) bill of health instead of encodable=False."""
    source = "\n".join([
        "remember a number called alpha with 10",
        "remember a number called beta with 2",
        "remember a value called doubled from beta multiplied by beta",
        "forbid alpha is above doubled",
    ])
    result = checker.check_source(source)
    assert isinstance(result, checker.CheckResult)
    assert result.encodable is False
    assert result.skipped_reason is not None
    assert "doubled" in result.skipped_reason


def test_check_source_unparseable_source_returns_checked_zero_no_raise():
    result = checker.check_source("gibberish nonsense flarn blorp")
    assert isinstance(result, checker.CheckResult)
    assert result.checked == 0
    assert result.findings == []

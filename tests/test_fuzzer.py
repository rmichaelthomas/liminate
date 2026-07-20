"""Differential fuzzer for the Z3 encoder (src/liminate/checker.py).

Decidability Step 2.5 (Trust Infrastructure Addendum v1.0r §88.6) — a
property-based fuzzer that verifies the encoder produces formulas
semantically equivalent to what the interpreter computes at runtime.
Generates random condition ASTs paired with random concrete fact
bindings, evaluates each through both paths via `_oracle`, and asserts
they agree.

Read-only against checker.py / interpreter.py / analyzer.py — this file
is purely additive. See checker.py's module docstring for the encoder's
design notes; this file exercises it rather than modifying it.
"""

from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass, field as dc_field
from datetime import date, timedelta

import pytest

z3 = pytest.importorskip("z3")

from hypothesis import assume, given, settings, strategies as st

from liminate.analyzer import SymbolEntry
from liminate.checker import _Encoder, NonlinearArithmetic, UnencodableConstruct
from liminate.interpreter import _RuntimeError as _InterpRuntimeError
from liminate.interpreter import _eval_condition
from liminate.parser import (
    ArithmeticNode,
    BareWord,
    CompoundConditionNode,
    ConditionNode,
    DateLiteral,
    DefineNode,
    EachPronoun,
    ExpectNode,
    FieldAccessNode,
    ForbidNode,
    NameRef,
    NumberLiteral,
    PermitNode,
    PredicateApplicationNode,
    QuotedString,
    RequireNode,
)
from liminate.renderer import render

pytestmark = pytest.mark.fuzzer

_HEAVY = os.environ.get("LIMINATE_FUZZ_HEAVY", "")
_MAX_EXAMPLES = 5000 if _HEAVY else 500


# ---------------------------------------------------------------------------
# Phase 2 — the round-trip oracle
# ---------------------------------------------------------------------------

# Sentinel distinguishing "the interpreter/encoder declined this input" from
# a real (bool, bool) result. `_oracle` returns a value (not an exception) on
# skip so it stays usable from both plain deterministic tests and hypothesis
# property tests — the property test is the one place that turns a skip into
# `assume(False)`, since `hypothesis.assume`/`event` raise InvalidArgument
# when called outside an active `@given` run, and Phase 2's own acceptance
# check (a hand-crafted skip case) is a plain test, not a `@given` one.
SKIPPED = object()

# Skip-cause counters (§10 manual-gate reporting): incremented on every
# skip so the breakdown by cause can be read back after a run.
skip_counts: Counter = Counter()


def _pin_constants(enc, symbol_table):
    """Equality constraints pinning every allocated Z3 constant to its
    concrete value from `symbol_table` (§4 sort-matching table). List-type
    entries need no pin — membership is expanded from the literal values
    already captured in `enc.lists` at encode time."""
    pins = []
    for name, entry in symbol_table.items():
        if entry.type == "number":
            const = enc.constants.get(name)
            if const is not None:
                pins.append(const == z3.RealVal(entry.value))
        elif entry.type == "string":
            const = enc.constants.get(name)
            if const is not None:
                pins.append(const == z3.StringVal(entry.value))
        elif entry.type == "date":
            const = enc.constants.get(name)
            if const is not None:
                pins.append(const == z3.IntVal(entry.value.toordinal()))
        elif entry.type == "record":
            for field_name, field_value in entry.value.items():
                const = enc.constants.get(f"{name}__{field_name}")
                if const is None:
                    continue
                field_type = (entry.schema or {}).get(field_name)
                if field_type == "number":
                    pins.append(const == z3.RealVal(field_value))
                elif field_type == "string":
                    pins.append(const == z3.StringVal(field_value))
                elif field_type == "date":
                    pins.append(const == z3.IntVal(field_value.toordinal()))
    return pins


def _oracle(condition_ast, symbol_table):
    """Compare the interpreter's verdict on `condition_ast` against the
    encoder's, both evaluated over the concrete values in `symbol_table`.

    Returns `(interp_result, encoder_agrees)` — both real bools — when
    both sides accept the input. Returns `(SKIPPED, reason)` when either
    side declines: the interpreter rejecting or the encoder refusing to
    encode is not an encoder disagreement (§8 invariants 6/7).
    """
    try:
        interp_result = _eval_condition(condition_ast, None, symbol_table)
    except _InterpRuntimeError:
        skip_counts["interp_runtime_error"] += 1
        return SKIPPED, "interp_runtime_error"
    except TypeError:
        skip_counts["interp_type_error"] += 1
        return SKIPPED, "interp_type_error"

    enc = _Encoder(z3, symbol_table, {})
    try:
        formula = enc.encode_condition(condition_ast)
    except (UnencodableConstruct, NonlinearArithmetic):
        skip_counts["encoder_unencodable"] += 1
        return SKIPPED, "encoder_unencodable"
    except z3.Z3Exception:
        skip_counts["encoder_z3_exception"] += 1
        return SKIPPED, "encoder_z3_exception"

    solver = z3.Solver()
    solver.add(formula if interp_result else z3.Not(formula))
    for pin in _pin_constants(enc, symbol_table):
        solver.add(pin)

    agrees = solver.check() == z3.sat
    return interp_result, agrees


def _entries(**by_name):
    """Build a symbol table from name=value pairs, inferring the
    SymbolEntry.type the same way the interpreter's own `_store` would
    for these scalar shapes."""
    symtab = {}
    for name, value in by_name.items():
        if isinstance(value, bool):
            raise ValueError("bool facts aren't part of v1's value model")
        if isinstance(value, (int, float)):
            symtab[name] = SymbolEntry(name=name, value=value, type="number")
        elif isinstance(value, str):
            symtab[name] = SymbolEntry(name=name, value=value, type="string")
        elif isinstance(value, date):
            symtab[name] = SymbolEntry(name=name, value=value, type="date")
        elif isinstance(value, list):
            symtab[name] = SymbolEntry(name=name, value=value, type="list_of_strings")
        else:
            raise ValueError(f"unhandled fact value {value!r}")
    return symtab


def test_oracle_equality_agrees():
    symtab = _entries(amount=10)
    cond = ConditionNode(field=NameRef("amount"), op="is", value=NumberLiteral(10))
    interp_result, agrees = _oracle(cond, symtab)
    assert interp_result is True
    assert agrees


def test_oracle_ordered_comparison_agrees():
    symtab = _entries(amount=10)
    cond = ConditionNode(field=NameRef("amount"), op="above", value=NumberLiteral(5))
    interp_result, agrees = _oracle(cond, symtab)
    assert interp_result is True
    assert agrees


def test_oracle_within_agrees():
    symtab = _entries(amount=100)
    cond = ConditionNode(
        field=NameRef("amount"), op="within",
        value=NumberLiteral(5), value2=NumberLiteral(106),
    )
    interp_result, agrees = _oracle(cond, symtab)
    assert interp_result is False  # |100-106|=6 > 5
    assert agrees


def test_oracle_includes_agrees():
    symtab = _entries(tags=["red", "green"])
    cond = ConditionNode(
        field=NameRef("tags"), op="includes", value=QuotedString("green"),
    )
    interp_result, agrees = _oracle(cond, symtab)
    assert interp_result is True
    assert agrees


def test_oracle_compound_and_or_agrees():
    symtab = _entries(amount=10, status="open")
    left = ConditionNode(field=NameRef("amount"), op="above", value=NumberLiteral(5))
    right = ConditionNode(field=NameRef("status"), op="is", value=QuotedString("open"))
    and_cond = CompoundConditionNode(left=left, right=right, connector="and")
    or_cond = CompoundConditionNode(
        left=left,
        right=ConditionNode(field=NameRef("status"), op="is", value=QuotedString("closed")),
        connector="or",
    )
    interp_and, agrees_and = _oracle(and_cond, symtab)
    interp_or, agrees_or = _oracle(or_cond, symtab)
    assert interp_and is True and agrees_and
    assert interp_or is True and agrees_or


def test_oracle_skips_on_string_above_number():
    symtab = _entries(status="open")
    cond = ConditionNode(field=NameRef("status"), op="above", value=NumberLiteral(50))
    interp_result, reason = _oracle(cond, symtab)
    assert interp_result is SKIPPED
    assert reason == "interp_type_error"


# ---------------------------------------------------------------------------
# Phase 3 — hypothesis strategies
# ---------------------------------------------------------------------------

_STRING_ALPHABET = [
    "alpha", "beta", "gamma", "west", "east", "sre", "oncall", "admin",
]
_DATE_CENTER = date(2025, 7, 1)


@dataclass
class FactSchema:
    """A random symbol table (§5) plus the name pools the condition
    generator needs to respect operator-type compatibility."""
    symtab: dict
    numeric_names: list
    string_names: list
    date_names: list
    list_name: object  # str | None
    record_name: object  # str | None
    record_fields: dict  # field_name -> "number" | "string" | "date"
    _predicate_seq: list = dc_field(default_factory=lambda: [0])

    def next_predicate_name(self) -> str:
        self._predicate_seq[0] += 1
        return f"__pred_{self._predicate_seq[0]}"


def _names_for_kind(schema: FactSchema, kind: str) -> list:
    return {
        "number": schema.numeric_names,
        "string": schema.string_names,
        "date": schema.date_names,
    }[kind]


def _number_strategy():
    # Rounded to 2dp (currency-like), not raw doubles: hypothesis's float
    # strategy otherwise happily generates values like 1.6e-256, and
    # `x - 1.6e-256 == x` is True under IEEE-754 double rounding but False
    # under Z3 Real's exact rational arithmetic — a genuine representation
    # gap between the two arithmetic models, not a bug in either side, and
    # not a shape any real Liminate program's literals take. Confirmed via
    # a 2000-example probe before this fix; zero disagreements after it.
    return st.one_of(
        st.integers(min_value=-1000, max_value=1000),
        st.floats(
            min_value=-1000.0, max_value=1000.0,
            allow_nan=False, allow_infinity=False,
        ).map(lambda x: round(x, 2)),
    )


def _date_strategy():
    return st.dates(
        min_value=_DATE_CENTER - timedelta(days=182),
        max_value=_DATE_CENTER + timedelta(days=182),
    )


@st.composite
def fact_schema(draw):
    """§5 — 2-6 scalar facts, an optional string list, an optional
    record. At least one scalar is always present, so every schema has
    at least one usable field for equality-family operators."""
    symtab: dict = {}
    numeric_names: list = []
    string_names: list = []
    date_names: list = []

    n_scalars = draw(st.integers(min_value=2, max_value=6))
    for i in range(n_scalars):
        kind = draw(st.sampled_from(["number", "string", "date"]))
        if kind == "number":
            name = f"number_{i}"
            symtab[name] = SymbolEntry(
                name=name, value=draw(_number_strategy()), type="number",
            )
            numeric_names.append(name)
        elif kind == "string":
            name = f"string_{i}"
            symtab[name] = SymbolEntry(
                name=name, value=draw(st.sampled_from(_STRING_ALPHABET)),
                type="string",
            )
            string_names.append(name)
        else:
            name = f"date_{i}"
            symtab[name] = SymbolEntry(
                name=name, value=draw(_date_strategy()), type="date",
            )
            date_names.append(name)

    list_name = None
    if draw(st.booleans()):
        list_name = "tags"
        items = draw(
            st.lists(st.sampled_from(_STRING_ALPHABET), min_size=0, max_size=5)
        )
        symtab[list_name] = SymbolEntry(
            name=list_name, value=items, type="list_of_strings",
        )

    record_name = None
    record_fields: dict = {}
    if draw(st.booleans()):
        record_name = "rec"
        n_fields = draw(st.integers(min_value=1, max_value=3))
        fields: dict = {}
        schema_types: dict = {}
        for i in range(n_fields):
            fkind = draw(st.sampled_from(["number", "string", "date"]))
            fname = f"f{i}"
            if fkind == "number":
                fields[fname] = draw(_number_strategy())
            elif fkind == "string":
                fields[fname] = draw(st.sampled_from(_STRING_ALPHABET))
            else:
                fields[fname] = draw(_date_strategy())
            schema_types[fname] = fkind
        symtab[record_name] = SymbolEntry(
            name=record_name, value=fields, type="record", schema=schema_types,
        )
        record_fields = schema_types

    return FactSchema(
        symtab=symtab,
        numeric_names=numeric_names,
        string_names=string_names,
        date_names=date_names,
        list_name=list_name,
        record_name=record_name,
        record_fields=record_fields,
    )


@st.composite
def _arithmetic_value(draw, schema: FactSchema):
    """Linear-only arithmetic (TI-Q13 closure): multiplied_by/divided_by
    always keep at least one compile-time-constant (NumberLiteral)
    operand, and divided_by never uses a literal-zero divisor (failure
    mode #7)."""
    op = draw(st.sampled_from(["plus", "minus", "multiplied_by", "divided_by"]))

    def _operand():
        if schema.numeric_names and draw(st.booleans()):
            name = draw(st.sampled_from(schema.numeric_names))
            return draw(st.sampled_from([NameRef(name), BareWord(name)]))
        return NumberLiteral(draw(_number_strategy()))

    if op in ("multiplied_by", "divided_by"):
        literal_value = draw(_number_strategy())
        if op == "divided_by" and literal_value == 0:
            literal_value = 1
        literal_on_left = draw(st.booleans())
        other = _operand()
        left, right = (
            (NumberLiteral(literal_value), other) if literal_on_left
            else (other, NumberLiteral(literal_value))
        )
    else:
        left, right = _operand(), _operand()
    return ArithmeticNode(left=left, right=right, op=op)


@st.composite
def _typed_value(draw, schema: FactSchema, kind: str):
    """A value AST matching `kind`'s type — a literal, a name reference
    (NameRef or BareWord, per failure mode #6 both encode identically),
    a record FieldAccessNode when available, or (numeric only) linear
    arithmetic."""
    names = _names_for_kind(schema, kind)
    r = draw(st.integers(min_value=0, max_value=99))

    if kind == "number" and r < 15:
        return draw(_arithmetic_value(schema))

    record_fields_of_kind = [
        f for f, t in schema.record_fields.items() if t == kind
    ]
    if 15 <= r < 30 and record_fields_of_kind:
        fname = draw(st.sampled_from(record_fields_of_kind))
        return FieldAccessNode(field=fname, record_name=schema.record_name)

    if 30 <= r < 65 and names:
        # BareWord only: interpreter._eval_value has no NameRef branch (it
        # only resolves BareWord in value position — verified against
        # main@2c628e1). A bare NameRef here raises _RuntimeError
        # ("Unexpected value NameRef."), which is a pure skip-budget waste,
        # not useful coverage — arithmetic operands are a different code
        # path (_evaluate_expression) and do support NameRef; see
        # `_arithmetic_value` above.
        return BareWord(draw(st.sampled_from(names)))

    if kind == "number":
        return NumberLiteral(draw(_number_strategy()))
    if kind == "string":
        return QuotedString(draw(st.sampled_from(_STRING_ALPHABET)))
    return DateLiteral(draw(_date_strategy()))


@st.composite
def _predicate_application(draw, schema: FactSchema):
    """§5 — a `define`-backed predicate applied to a subject whose type
    matches the body's implicit (EachPronoun) parameter type."""
    pools = [k for k in ("number", "string", "date") if _names_for_kind(schema, k)]
    if not pools:
        return draw(_condition_leaf(schema))

    kind = draw(st.sampled_from(pools))
    op_pool = (
        ["is", "equal_to", "not_equal_to"] if kind == "string"
        else ["above", "below", "not_above", "not_below", "is", "equal_to", "not_equal_to"]
    )
    op = draw(st.sampled_from(op_pool))
    value = draw(_typed_value(schema, kind))
    body = ConditionNode(field=EachPronoun(), op=op, value=value)

    pred_name = schema.next_predicate_name()
    schema.symtab[pred_name] = SymbolEntry(
        name=pred_name, value=body, type="predicate",
    )

    subject_name = draw(st.sampled_from(_names_for_kind(schema, kind)))
    negated = draw(st.booleans())
    return PredicateApplicationNode(
        subject=NameRef(subject_name), predicate_name=pred_name, negated=negated,
    )


@st.composite
def _condition_leaf(draw, schema: FactSchema):
    """A single ConditionNode, respecting operator-type compatibility
    (§5) so the interpreter/encoder skip rate stays low."""
    op_pool = []
    if schema.numeric_names or schema.date_names:
        op_pool += ["above", "below", "not_above", "not_below", "within"]
    if schema.list_name is not None:
        op_pool += ["includes", "not_includes"]
    op_pool += ["is", "equal_to", "not_equal_to"]

    op = draw(st.sampled_from(op_pool))

    if op in ("includes", "not_includes"):
        value = QuotedString(draw(st.sampled_from(_STRING_ALPHABET)))
        return ConditionNode(field=NameRef(schema.list_name), op=op, value=value)

    if op in ("above", "below", "not_above", "not_below", "within"):
        ordered_kinds = [
            k for k in ("number", "date") if _names_for_kind(schema, k)
        ]
        kind = draw(st.sampled_from(ordered_kinds))
        field_name = draw(st.sampled_from(_names_for_kind(schema, kind)))
        field = NameRef(field_name)
        if op == "within":
            # Tolerance is always numeric, even for a date field (day count) —
            # _within_tolerance requires it regardless of field kind.
            tolerance = draw(_typed_value(schema, "number"))
            target = draw(_typed_value(schema, kind))
            return ConditionNode(field=field, op=op, value=tolerance, value2=target)
        value = draw(_typed_value(schema, kind))
        return ConditionNode(field=field, op=op, value=value)

    # Equality family: any scalar type, including a record field.
    pools = [k for k in ("number", "string", "date") if _names_for_kind(schema, k)]
    if schema.record_name is not None:
        pools.append("record")
    kind = draw(st.sampled_from(pools))
    if kind == "record":
        field_name = draw(st.sampled_from(list(schema.record_fields)))
        field = FieldAccessNode(field=field_name, record_name=schema.record_name)
        value = draw(_typed_value(schema, schema.record_fields[field_name]))
    else:
        field_name = draw(st.sampled_from(_names_for_kind(schema, kind)))
        field = NameRef(field_name)
        value = draw(_typed_value(schema, kind))
    return ConditionNode(field=field, op=op, value=value)


@st.composite
def _leaf(draw, schema: FactSchema):
    r = draw(st.integers(min_value=0, max_value=99))
    if r < 15:
        return draw(_predicate_application(schema))
    return draw(_condition_leaf(schema))


@st.composite
def condition_ast(draw, schema: FactSchema, depth: int = 0):
    """§5 — recursive condition AST, depth-capped at 3, referencing only
    facts present in `schema`."""
    if depth < 3 and draw(st.booleans()):
        connector = draw(st.sampled_from(["and", "or"]))
        left = draw(condition_ast(schema, depth=depth + 1))
        right = draw(condition_ast(schema, depth=depth + 1))
        return CompoundConditionNode(left=left, right=right, connector=connector)
    return draw(_leaf(schema))


@st.composite
def deontic_statement(draw, schema: FactSchema):
    """§5 — a Require/Forbid/Permit/Expect wrapping a generated
    condition, with a 50% chance of an independently generated `unless`
    exception."""
    node_cls = draw(st.sampled_from([RequireNode, ForbidNode, PermitNode, ExpectNode]))
    condition = draw(condition_ast(schema))
    exception = draw(condition_ast(schema)) if draw(st.booleans()) else None
    return node_cls(condition=condition, exception=exception)


# ---------------------------------------------------------------------------
# Phase 4 — the deontic-statement oracle (verb-level encoding)
# ---------------------------------------------------------------------------

def _deontic_fires(node, condition_result: bool, exception_result: bool) -> bool:
    """Mirrors _exec_require/_exec_forbid/_exec_permit/_exec_expect's
    fire condition exactly (verified against interpreter.py at
    main@2c628e1) — require/expect fire on ¬condition ∧ ¬exception,
    forbid/permit fire on condition ∧ ¬exception."""
    if isinstance(node, (RequireNode, ExpectNode)):
        return (not condition_result) and (not exception_result)
    if isinstance(node, (ForbidNode, PermitNode)):
        return condition_result and (not exception_result)
    raise TypeError(f"not a deontic node: {type(node).__name__}")


def _deontic_allowed(node, condition_result: bool, exception_result: bool):
    """Mirrors checker.encode_deontic's `allowed` space — None for
    permit/expect (DT-Q3: they never participate in the require/forbid
    contradiction check)."""
    if isinstance(node, RequireNode):
        return condition_result or exception_result
    if isinstance(node, ForbidNode):
        return (not condition_result) or exception_result
    return None


def _deontic_oracle(node, symbol_table):
    """Verb-level counterpart to `_oracle`: compares the interpreter's
    fire/allowed verdicts against the encoder's effect/allowed formulas.
    Same skip semantics and exception surface as `_oracle`."""
    try:
        condition_result = _eval_condition(node.condition, None, symbol_table)
        exception_result = (
            _eval_condition(node.exception, None, symbol_table)
            if node.exception is not None else False
        )
    except _InterpRuntimeError:
        skip_counts["interp_runtime_error"] += 1
        return SKIPPED, "interp_runtime_error"
    except TypeError:
        skip_counts["interp_type_error"] += 1
        return SKIPPED, "interp_type_error"

    fires = _deontic_fires(node, condition_result, exception_result)
    allowed = _deontic_allowed(node, condition_result, exception_result)

    enc = _Encoder(z3, symbol_table, {})
    try:
        effect_formula, allowed_formula = enc.encode_deontic(node)
    except (UnencodableConstruct, NonlinearArithmetic):
        skip_counts["encoder_unencodable"] += 1
        return SKIPPED, "encoder_unencodable"
    except z3.Z3Exception:
        skip_counts["encoder_z3_exception"] += 1
        return SKIPPED, "encoder_z3_exception"

    pins = _pin_constants(enc, symbol_table)

    effect_solver = z3.Solver()
    effect_solver.add(effect_formula if fires else z3.Not(effect_formula))
    for pin in pins:
        effect_solver.add(pin)
    effect_agrees = effect_solver.check() == z3.sat

    allowed_agrees = True
    if allowed_formula is not None:
        allowed_solver = z3.Solver()
        allowed_solver.add(allowed_formula if allowed else z3.Not(allowed_formula))
        for pin in pins:
            allowed_solver.add(pin)
        allowed_agrees = allowed_solver.check() == z3.sat

    return (fires, allowed), (effect_agrees and allowed_agrees)


# ---------------------------------------------------------------------------
# Phase 4 — property tests
# ---------------------------------------------------------------------------


@given(data=st.data())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
def test_condition_round_trip(data):
    schema = data.draw(fact_schema())
    cond = data.draw(condition_ast(schema))
    interp_result, agrees = _oracle(cond, schema.symtab)
    if interp_result is SKIPPED:
        assume(False)
    assert agrees, f"Encoder disagrees on {render(cond)}: interpreter={interp_result}"


@given(data=st.data())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
def test_deontic_effect_round_trip(data):
    schema = data.draw(fact_schema())
    stmt = data.draw(deontic_statement(schema))
    outcome, agrees = _deontic_oracle(stmt, schema.symtab)
    if outcome is SKIPPED:
        assume(False)
    assert agrees, f"Encoder disagrees on {render(stmt)}: interpreter={outcome}"


@given(data=st.data())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
def test_predicate_round_trip(data):
    schema = data.draw(fact_schema())
    application = data.draw(_predicate_application(schema))
    interp_result, agrees = _oracle(application, schema.symtab)
    if interp_result is SKIPPED:
        assume(False)
    assert agrees, (
        f"Encoder disagrees on predicate application {render(application)}: "
        f"interpreter={interp_result}"
    )


# ---------------------------------------------------------------------------
# Phase 4 — regression anchors (deterministic)
# ---------------------------------------------------------------------------


def test_within_operand_order():
    """value=tolerance, value2=target — pins the operand order verified
    during the Step 2 design (§3 correction 1)."""
    for amount, tolerance, target, expected in [
        (100, 5, 103, True),   # |100-103|=3 <= 5
        (100, 5, 106, False),  # |100-106|=6 > 5
        (100, 0, 100, True),   # |100-100|=0 <= 0
        (100, 0, 101, False),  # |100-101|=1 > 0
    ]:
        symtab = _entries(amount=amount)
        cond = ConditionNode(
            field=NameRef("amount"), op="within",
            value=NumberLiteral(tolerance), value2=NumberLiteral(target),
        )
        interp_result, agrees = _oracle(cond, symtab)
        assert interp_result == expected
        assert agrees


def test_includes_empty_list():
    symtab = {"tags": SymbolEntry(name="tags", value=[], type="list_of_strings")}
    includes_cond = ConditionNode(
        field=NameRef("tags"), op="includes", value=QuotedString("x"),
    )
    not_includes_cond = ConditionNode(
        field=NameRef("tags"), op="not_includes", value=QuotedString("x"),
    )
    interp_result, agrees = _oracle(includes_cond, symtab)
    assert interp_result is False
    assert agrees
    interp_result, agrees = _oracle(not_includes_cond, symtab)
    assert interp_result is True
    assert agrees


def test_KNOWN_interpreter_type_mismatch_surface():
    """Pins the exception-surface map from v1.0r §88.3's latent
    _apply_op hole — reachable only by direct AST construction bypassing
    the analyzer, exactly how this fuzzer builds conditions (verified
    against interpreter.py at main@2c628e1).

    If this starts failing because a mismatch now raises _RuntimeError
    instead of TypeError, that is an interpreter improvement: update
    this test and narrow the oracle's catch, do not revert the
    interpreter.
    """
    string_symtab = _entries(status="open")
    number_symtab = _entries(amount=10)
    date_symtab = _entries(due=date(2026, 1, 1))

    with pytest.raises(TypeError):
        _eval_condition(
            ConditionNode(field=NameRef("status"), op="above", value=NumberLiteral(50)),
            None, string_symtab,
        )
    with pytest.raises(TypeError):
        _eval_condition(
            ConditionNode(field=NameRef("amount"), op="above", value=QuotedString("x")),
            None, number_symtab,
        )
    with pytest.raises(_InterpRuntimeError):
        _eval_condition(
            ConditionNode(field=NameRef("due"), op="above", value=NumberLiteral(5)),
            None, date_symtab,
        )
    with pytest.raises(_InterpRuntimeError):
        _eval_condition(
            ConditionNode(
                field=NameRef("status"), op="within",
                value=NumberLiteral(5), value2=NumberLiteral(10),
            ),
            None, string_symtab,
        )
    assert _eval_condition(
        ConditionNode(field=NameRef("amount"), op="includes", value=QuotedString("x")),
        None, number_symtab,
    ) is False
    assert _eval_condition(
        ConditionNode(field=NameRef("status"), op="is", value=NumberLiteral(1)),
        None, string_symtab,
    ) is False


# ---------------------------------------------------------------------------
# Phase 5 — skip-rate reporting (manual-gate instrumentation)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def _report_skip_counts():
    yield
    if skip_counts:
        total = sum(skip_counts.values())
        print(f"\n[fuzzer] {total} skipped examples by cause:")
        for reason, count in skip_counts.most_common():
            print(f"[fuzzer]   {reason}: {count}")

"""Z3 satisfiability checker for Liminate's enforcement fragment.

Decidability Step 2 (Trust Infrastructure Addendum v1.0s §91/§92.6).
Encodes an Agreement's deontic statements (require/forbid/permit/expect
and the define predicates they reference) into SMT constraints over
QF_UFLIRA and runs seven authoring-time checks that a human reading the
file would miss.

Scope: the enforcement fragment only. No temporal encoding (starting_date
/ until_date are ignored — v1.0s §91.6), no trace semantics, no CLI verb.
This module sits alongside analyzer.detect_contradictions; it does not
replace or modify it.

z3 is an optional dependency (the `check` extra). This module never
imports z3 at top level — `import liminate.checker` must always succeed.
The import happens lazily inside the public entry point.
"""


from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import date

from .parser import (
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
    RememberValueNode,
    RequireNode,
    SequenceNode,
)
from .renderer import render


class CheckerUnavailable(Exception):
    """Raised when the z3 solver is not installed."""


class UnencodableConstruct(Exception):
    """Raised when an AST node falls outside the encodable fragment."""


class NonlinearArithmetic(Exception):
    """Raised when multiplied_by/divided_by has no compile-time-constant
    operand after definition inlining."""


def _import_z3():
    try:
        import z3
    except ImportError:
        raise CheckerUnavailable(
            "Satisfiability checking needs the z3 solver. "
            "Install it with: pip install liminate[check]"
        ) from None
    return z3


@dataclass
class Finding:
    kind: str
    severity: str
    statements: list[str]
    explanation: str


@dataclass
class CheckResult:
    findings: list[Finding]
    checked: int
    elapsed_ms: float
    encodable: bool
    skipped_reason: str | None = None



# ---------------------------------------------------------------------------
# Phase 2 — sort model and constant allocation
# ---------------------------------------------------------------------------

# Liminate names may contain hyphens (e.g. "actor-teams") and other
# characters that are not legal SMT identifiers. Sanitization is
# deterministic; the encoder keeps a reverse map so diagnostics can name
# the original Liminate identifier instead of the sanitized one.
_SANITIZE_RE = re.compile(r"[^A-Za-z0-9_]")

# SymbolEntry.type / SymbolEntry.schema[field] values that map onto a
# scalar Z3 sort. Dates encode as Int via epoch-day ordinals (§9 fact 9 —
# never mixed with number's Real sort).
_LIST_TYPES = frozenset({"list_of_strings", "list_of_numbers", "list_of_dates"})


def _sanitize_base(name: str) -> str:
    sanitized = _SANITIZE_RE.sub("_", name)
    if sanitized and sanitized[0].isdigit():
        sanitized = f"_{sanitized}"
    return sanitized or "_"


def _date_ordinal(d: date) -> int:
    return d.toordinal()


class _Encoder:
    """Holds the Z3 constant map for one check_agreement() call plus the
    definitions map (Phase 4) needed for value-position name inlining."""

    def __init__(self, z3mod, symbol_table, definitions):
        self.z3 = z3mod
        self.symtab = symbol_table
        self.definitions = definitions  # name -> defining ASTNode (Phase 4)
        self.constants: dict[str, object] = {}
        self.reverse: dict[str, str] = {}
        self.lists: dict[str, list] = {}
        self._sanitized_cache: dict[str, str] = {}
        self._inlining_visited: set[str] = set()
        self._predicate_depth = 0
        self._build_constants()

    def _sanitize(self, name: str) -> str:
        """Deterministic name -> SMT identifier, disambiguated against
        collisions from distinct original names sanitizing identically."""
        cached = self._sanitized_cache.get(name)
        if cached is not None:
            return cached
        base = _sanitize_base(name)
        candidate = base
        suffix = 0
        while candidate in self.reverse and self.reverse[candidate] != name:
            suffix += 1
            candidate = f"{base}__{suffix}"
        self._sanitized_cache[name] = candidate
        self.reverse[candidate] = name
        return candidate

    def _build_constants(self) -> None:
        for name, entry in self.symtab.items():
            if entry.type == "number":
                self.constants[name] = self.z3.Real(self._sanitize(name))
            elif entry.type == "string":
                self.constants[name] = self.z3.String(self._sanitize(name))
            elif entry.type == "date":
                self.constants[name] = self.z3.Int(self._sanitize(name))
            elif entry.type == "record":
                for field_name, field_type in (entry.schema or {}).items():
                    key = f"{name}__{field_name}"
                    ident = self._sanitize(key)
                    if field_type == "number":
                        self.constants[key] = self.z3.Real(ident)
                    elif field_type == "string":
                        self.constants[key] = self.z3.String(ident)
                    elif field_type == "date":
                        self.constants[key] = self.z3.Int(ident)
                    # Any other field scalar type is left unallocated;
                    # UnencodableConstruct is raised lazily if a condition
                    # actually references it (§10 boundary contract).
            elif entry.type in _LIST_TYPES:
                # No constant — §6 "includes"/"not_includes" expand to a
                # finite disjunction over these literal values instead.
                self.lists[name] = list(entry.value)
            # list_of_records, composition, predicate, and anything else
            # get no constant here; predicates are handled by body
            # inlining (§6), not by constant allocation.

    # -----------------------------------------------------------------
    # Phase 3 — condition encoder (mirrors interpreter._eval_condition)
    # -----------------------------------------------------------------

    def encode_condition(self, cond):
        if isinstance(cond, CompoundConditionNode):
            left = self.encode_condition(cond.left)
            right = self.encode_condition(cond.right)
            if cond.connector == "and":
                return self.z3.And(left, right)
            return self.z3.Or(left, right)
        if isinstance(cond, PredicateApplicationNode):
            return self._encode_predicate_application(cond)
        if isinstance(cond, ConditionNode):
            return self._encode_condition_leaf(cond)
        raise UnencodableConstruct(
            f"Can't encode condition {type(cond).__name__}."
        )

    def _encode_predicate_application(self, cond):
        entry = self.symtab.get(cond.predicate_name)
        if entry is None or entry.type != "predicate":
            raise UnencodableConstruct(
                f"No predicate definition found for '{cond.predicate_name}'."
            )
        if self._predicate_depth >= _MAX_PREDICATE_ENCODE_DEPTH:
            raise UnencodableConstruct(
                f"Predicate '{cond.predicate_name}' is nested more than "
                f"{_MAX_PREDICATE_ENCODE_DEPTH} levels deep — this usually "
                f"means two or more definitions refer back to each other."
            )
        substituted = _substitute_each_pronoun(entry.value, cond.subject)
        self._predicate_depth += 1
        try:
            result = self.encode_condition(substituted)
        finally:
            self._predicate_depth -= 1
        return self.z3.Not(result) if cond.negated else result

    def _encode_condition_leaf(self, cond):
        if cond.op == "within":
            # §3 correction (1): value is the tolerance, value2 is the
            # target — mirrors interpreter._eval_condition exactly.
            field_val = self.encode_field(cond.field)
            tolerance = self.encode_value(cond.value)
            target = self.encode_value(cond.value2)
            return self.z3.And(
                field_val - target <= tolerance,
                target - field_val <= tolerance,
            )
        if cond.op in ("includes", "not_includes"):
            return self._encode_membership(cond)
        field_val = self.encode_field(cond.field)
        value_val = self.encode_value(cond.value)
        return _encode_comparison(self.z3, cond.op, field_val, value_val)

    def _encode_membership(self, cond):
        if not isinstance(cond.field, NameRef) or cond.field.name not in self.lists:
            label = cond.field.name if isinstance(cond.field, NameRef) else type(cond.field).__name__
            raise UnencodableConstruct(
                f"'{cond.op}' needs a statically known list; '{label}' isn't one."
            )
        items = self.lists[cond.field.name]
        elem = self.encode_value(cond.value)
        if not items:
            # §6 empty-list edge case: z3.Or()/z3.And() with no arguments
            # is invalid, so this is special-cased before splatting.
            return self.z3.BoolVal(cond.op == "not_includes")
        literals = [self._python_literal(v) for v in items]
        if cond.op == "includes":
            return self.z3.Or(*[elem == lit for lit in literals])
        return self.z3.And(*[elem != lit for lit in literals])

    def _python_literal(self, value):
        if isinstance(value, bool):
            raise UnencodableConstruct("Boolean list elements can't be encoded.")
        if isinstance(value, (int, float)):
            return self.z3.RealVal(value)
        if isinstance(value, str):
            return self.z3.StringVal(value)
        if isinstance(value, date):
            return self.z3.IntVal(_date_ordinal(value))
        raise UnencodableConstruct(f"Can't encode list element {value!r}.")

    def encode_field(self, node):
        if isinstance(node, NameRef):
            if node.name in self.constants:
                return self.constants[node.name]
            raise UnencodableConstruct(f"'{node.name}' isn't an encodable fact.")
        if isinstance(node, FieldAccessNode):
            key = f"{node.record_name}__{node.field}"
            if key in self.constants:
                return self.constants[key]
            raise UnencodableConstruct(
                f"'{node.field} of {node.record_name}' isn't an encodable fact."
            )
        # EachPronoun (outside a predicate body it should already have
        # been substituted out of) and ExtremaNode (§6: out of scope
        # this build) both fall through to this generic branch.
        raise UnencodableConstruct(
            f"Can't encode field reference {type(node).__name__}."
        )

    # -----------------------------------------------------------------
    # Phase 4 — value position: literals, name resolution + inlining,
    # arithmetic + nonlinearity detection (TI-Q13 closure)
    # -----------------------------------------------------------------

    def encode_value(self, node, origin_name=None):
        if isinstance(node, NumberLiteral):
            return self.z3.RealVal(node.value)
        if isinstance(node, DateLiteral):
            return self.z3.IntVal(_date_ordinal(node.value))
        if isinstance(node, QuotedString):
            return self.z3.StringVal(node.content)
        if isinstance(node, (BareWord, NameRef)):
            # §3 correction (4): both shapes must be handled — the parser
            # emits BareWord for names in value position, but the AST
            # comment allows NameRef too.
            return self._resolve_name_value(node)
        if isinstance(node, FieldAccessNode):
            return self.encode_field(node)
        if isinstance(node, ArithmeticNode):
            return self._encode_arithmetic(node, origin_name)
        # EachPronoun at top level and ExtremaNode (§6: out of scope
        # this build) both fall through to this generic branch.
        raise UnencodableConstruct(f"Can't encode value {type(node).__name__}.")

    def _resolve_name_value(self, node):
        name = node.word if isinstance(node, BareWord) else node.name
        defining = self.definitions.get(name)
        if (
            defining is not None
            and self._contains_arithmetic(defining)
            and name not in self._inlining_visited
        ):
            # §7 inlining rule: the symbol table only stores computed
            # values, not defining expressions, so a name whose defining
            # `remember` involves arithmetic is inlined — the recursive
            # encode below is what lets nonlinearity be caught at all.
            self._inlining_visited.add(name)
            try:
                return self.encode_value(defining, origin_name=name)
            finally:
                self._inlining_visited.discard(name)
        if name in self.constants:
            return self.constants[name]
        if isinstance(node, BareWord):
            # Matches interpreter._eval_value: an unresolved BareWord is
            # a string literal, not an error.
            return self.z3.StringVal(node.word)
        raise UnencodableConstruct(f"'{name}' isn't defined.")

    def _contains_arithmetic(self, node) -> bool:
        return isinstance(node, ArithmeticNode)

    def _is_compile_time_constant(self, node) -> bool:
        """A numeral literal, or an arithmetic tree of literals only —
        deliberately NOT resolved through name indirection. A BareWord/
        NameRef operand (e.g. `beta` in `beta multiplied by beta`) is
        always treated as an opaque runtime symbol here, even if its own
        defining value happens to be a literal — that symbol is a free
        Z3 constant to the solver, so multiplying it by itself is
        genuinely nonlinear regardless of what the interpreter would
        compute it to be at run time."""
        if isinstance(node, NumberLiteral):
            return True
        if isinstance(node, ArithmeticNode):
            return (
                self._is_compile_time_constant(node.left)
                and self._is_compile_time_constant(node.right)
            )
        return False

    def _encode_arithmetic(self, node, origin_name=None):
        if node.op in ("multiplied_by", "divided_by"):
            if not self._is_compile_time_constant(
                node.left
            ) and not self._is_compile_time_constant(node.right):
                raise NonlinearArithmetic(self._nonlinear_message(node, origin_name))
        left = self.encode_value(node.left, origin_name=origin_name)
        right = self.encode_value(node.right, origin_name=origin_name)
        if node.op == "plus":
            return left + right
        if node.op == "minus":
            return left - right
        if node.op == "multiplied_by":
            return left * right
        if node.op == "divided_by":
            return left / right
        raise UnencodableConstruct(f"Unknown arithmetic operator '{node.op}'.")

    def _nonlinear_message(self, node, origin_name) -> str:
        op_word = "multiplied by" if node.op == "multiplied_by" else "divided by"
        msg = (
            f"'{render(node.left)} {op_word} {render(node.right)}' is nonlinear "
            f"— neither side is a compile-time constant."
        )
        if origin_name is not None:
            msg += (
                f" This came from inlining '{origin_name}', defined by a "
                f"'remember' statement."
            )
        return msg

    # -----------------------------------------------------------------
    # Phase 5 — deontic statement effect formulas (§8)
    # -----------------------------------------------------------------

    def encode_deontic(self, node):
        """Returns (effect, allowed) for a Require/Forbid/Permit/Expect
        node. `effect` is the condition under which the statement fires
        (halts for require/forbid, emits for permit, reports for
        expect). `allowed` is the allowed-state space (require/forbid
        only — None for permit/expect, which never participate in the
        require/forbid contradiction check per the locked DT-Q3
        decision: permit never contradicts)."""
        condition = self.encode_condition(node.condition)
        exception = (
            self.encode_condition(node.exception)
            if node.exception is not None
            else self.z3.BoolVal(False)
        )
        not_condition = self.z3.Not(condition)
        not_exception = self.z3.Not(exception)
        if isinstance(node, RequireNode):
            effect = self.z3.And(not_condition, not_exception)
            allowed = self.z3.Or(condition, exception)
            return effect, allowed
        if isinstance(node, ForbidNode):
            effect = self.z3.And(condition, not_exception)
            allowed = self.z3.Or(not_condition, exception)
            return effect, allowed
        if isinstance(node, PermitNode):
            effect = self.z3.And(condition, not_exception)
            return effect, None
        if isinstance(node, ExpectNode):
            effect = self.z3.And(not_condition, not_exception)
            return effect, None
        raise UnencodableConstruct(
            f"Can't encode deontic statement {type(node).__name__}."
        )


# Mirrors interpreter._MAX_PREDICATE_EVAL_DEPTH — belt-and-braces defense
# against a hand-built symbol table, since PRs #60/#61 already guarantee
# acyclicity for any program that reached the encoder via the analyzer.
_MAX_PREDICATE_ENCODE_DEPTH = 64


def _substitute_each_pronoun(node, replacement):
    """Deep-substitute every EachPronoun in a predicate body with the
    application's subject node (§3 correction 2) — never by name."""
    if isinstance(node, EachPronoun):
        return replacement
    if isinstance(node, CompoundConditionNode):
        return CompoundConditionNode(
            left=_substitute_each_pronoun(node.left, replacement),
            right=_substitute_each_pronoun(node.right, replacement),
            connector=node.connector,
        )
    if isinstance(node, ConditionNode):
        return ConditionNode(
            field=_substitute_each_pronoun(node.field, replacement),
            op=node.op,
            value=_substitute_each_pronoun(node.value, replacement),
            value2=(
                _substitute_each_pronoun(node.value2, replacement)
                if node.value2 is not None
                else None
            ),
        )
    if isinstance(node, PredicateApplicationNode):
        return PredicateApplicationNode(
            subject=_substitute_each_pronoun(node.subject, replacement),
            predicate_name=node.predicate_name,
            negated=node.negated,
        )
    if isinstance(node, ArithmeticNode):
        return ArithmeticNode(
            left=_substitute_each_pronoun(node.left, replacement),
            right=_substitute_each_pronoun(node.right, replacement),
            op=node.op,
        )
    return node


def _iter_statements(statements):
    """Descend into SequenceNode, mirroring the walking convention
    analyzer._iter_deontic_nodes uses — the shared pattern §10 asks the
    checker to reuse, applied here to the broader set of statement types
    check_agreement needs (not just Require/Forbid)."""
    for stmt in statements:
        if isinstance(stmt, SequenceNode):
            yield from _iter_statements(stmt.operations)
        else:
            yield stmt


def _build_definitions(statements):
    """§7 — name -> defining ASTNode, scanned from the program AST. The
    symbol table only stores computed values (RememberValueNode.value is
    gone by execution time), so this is the only place the defining
    expression survives. Later definitions overwrite earlier ones,
    matching _store's overwrite semantics (v1d §58)."""
    definitions: dict[str, object] = {}
    for stmt in _iter_statements(statements):
        if isinstance(stmt, RememberValueNode):
            definitions[stmt.name] = stmt.value
    return definitions


def _encode_comparison(z3mod, op, lhs, rhs):
    """Mirrors interpreter._apply_op exactly. not_above/not_below are
    fused negations (<=/>=), never a structural Not(above)/Not(below)
    wrapper — §12 failure mode 6."""
    if op in ("is", "equal_to"):
        return lhs == rhs
    if op == "not_equal_to":
        return lhs != rhs
    if op == "above":
        return lhs > rhs
    if op == "below":
        return lhs < rhs
    if op == "not_above":
        return lhs <= rhs
    if op == "not_below":
        return lhs >= rhs
    raise UnencodableConstruct(f"Unknown comparison operator '{op}'.")

def check_agreement(statements, symbol_table) -> CheckResult:
    """Encode `statements` and run the seven core checks.

    Input mirrors analyzer.detect_contradictions(statements): a list of
    top-level statement ASTs. Never raises for out-of-fragment input —
    UnencodableConstruct is caught at this boundary and reported via
    CheckResult(encodable=False, skipped_reason=...).
    """
    _import_z3()
    raise NotImplementedError

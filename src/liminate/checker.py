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

from .analyzer import SymbolEntry
from .lexer import LexError, leading_indent, tokenize
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
    parse,
)
from .renderer import render
from .reorderer import reorder
from .result import LiminateResult
from .run import run


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

    # -----------------------------------------------------------------
    # Phase 6, check 7 — a predicate's own body, standing alone
    # -----------------------------------------------------------------
    #
    # A `define` body is normally only ever encoded through an
    # application site (§6), where EachPronoun substitutes to a concrete
    # subject expression with a known sort. Check 7 asks whether the
    # body is constant *for any possible subject* — so it needs a fresh,
    # unconstrained Z3 constant standing in for "any subject," sorted by
    # how the body actually compares it. Reuses the same substitution +
    # encode_condition machinery as a real application by registering
    # the placeholder under a synthetic name in `self.constants`, rather
    # than inventing a second code path.

    def encode_predicate_body_standalone(self, predicate_name, body):
        sort = self._infer_subject_sort(body, set())
        if sort is None:
            raise UnencodableConstruct(
                f"Can't infer a subject type for predicate "
                f"'{predicate_name}' — its body never compares the "
                f"implicit subject against anything with a known sort."
            )
        placeholder = f"__subject__{predicate_name}"
        ident = self._sanitize(placeholder)
        if sort == "number":
            self.constants[placeholder] = self.z3.Real(ident)
        elif sort == "string":
            self.constants[placeholder] = self.z3.String(ident)
        else:
            self.constants[placeholder] = self.z3.Int(ident)
        substituted = _substitute_each_pronoun(body, NameRef(name=placeholder))
        return self.encode_condition(substituted)

    def _infer_subject_sort(self, node, visited):
        if isinstance(node, CompoundConditionNode):
            return self._infer_subject_sort(
                node.left, visited
            ) or self._infer_subject_sort(node.right, visited)
        if isinstance(node, ConditionNode):
            if isinstance(node.field, EachPronoun):
                hint = self._value_sort_hint(node.value)
                if hint is None and node.value2 is not None:
                    hint = self._value_sort_hint(node.value2)
                return hint
            return None
        if isinstance(node, PredicateApplicationNode):
            if isinstance(node.subject, EachPronoun):
                if node.predicate_name in visited:
                    return None
                entry = self.symtab.get(node.predicate_name)
                if entry is None or entry.type != "predicate":
                    return None
                return self._infer_subject_sort(
                    entry.value, visited | {node.predicate_name}
                )
            return None
        return None

    def _value_sort_hint(self, node):
        if isinstance(node, (NumberLiteral, ArithmeticNode)):
            return "number"
        if isinstance(node, DateLiteral):
            return "date"
        if isinstance(node, QuotedString):
            return "string"
        if isinstance(node, (BareWord, NameRef)):
            name = node.word if isinstance(node, BareWord) else node.name
            entry = self.symtab.get(name)
            if entry is not None and entry.type in ("number", "string", "date"):
                return entry.type
            return None
        return None


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


# ---------------------------------------------------------------------------
# Phase 6 — the seven core checks (§9)
# ---------------------------------------------------------------------------

_SOLVER_TIMEOUT_MS = 5000
_PAIRWISE_CAP = 200

_VERB_NAMES = {
    RequireNode: "require",
    ForbidNode: "forbid",
    PermitNode: "permit",
    ExpectNode: "expect",
}


@dataclass
class _DeonticEntry:
    index: int
    verb: str
    node: object
    effect: object
    allowed: object | None
    text: str


def _collect_deontic_entries(enc, statements) -> list[_DeonticEntry]:
    entries = []
    for stmt in _iter_statements(statements):
        verb = _VERB_NAMES.get(type(stmt))
        if verb is None:
            continue
        effect, allowed = enc.encode_deontic(stmt)
        entries.append(_DeonticEntry(
            index=len(entries), verb=verb, node=stmt,
            effect=effect, allowed=allowed, text=render(stmt),
        ))
    return entries


def _tracked_name(index, verb) -> str:
    return f"stmt_{index}_{verb}"


def _interpret_check_result(z3mod, result) -> str:
    if result == z3mod.unsat:
        return "unsat"
    if result == z3mod.sat:
        return "sat"
    return "unknown"


def _run_query(enc, tracked):
    """tracked: list[(formula, name)]. Every assertion is tracked (§9)
    so unsat_core() can map a finding back to its source statement(s).
    A per-query timeout means a hard query surfaces as 'unknown' rather
    than hanging the whole run."""
    s = enc.z3.Solver()
    s.set("timeout", _SOLVER_TIMEOUT_MS)
    for formula, name in tracked:
        s.assert_and_track(formula, name)
    status = _interpret_check_result(enc.z3, s.check())
    core = s.unsat_core() if status == "unsat" else None
    return status, core


def _inconclusive(check_name, statements) -> Finding:
    return Finding(
        kind="inconclusive", severity="info", statements=list(statements),
        explanation=(
            f"Check '{check_name}' timed out and is inconclusive for: "
            f"{', '.join(statements)}."
        ),
    )


def _cap_finding(count) -> Finding | None:
    if count <= _PAIRWISE_CAP:
        return None
    return Finding(
        kind="inconclusive", severity="info", statements=[],
        explanation=(
            f"{count} deontic statements exceeds the pairwise-check cap of "
            f"{_PAIRWISE_CAP} — require/forbid contradiction (check 3) and "
            f"redundant-forbid (check 5) were skipped. Per-statement checks "
            f"still ran."
        ),
    )


def _check_always_deny(enc, entries) -> list[Finding]:
    """Check 1 — a require whose allowed-space (C ∨ E) is UNSAT can
    never be satisfied: it always halts execution."""
    findings = []
    for e in entries:
        if e.verb != "require":
            continue
        status, _ = _run_query(enc, [(e.allowed, _tracked_name(e.index, e.verb))])
        if status == "unsat":
            findings.append(Finding(
                kind="always_deny", severity="error", statements=[e.text],
                explanation=(
                    f"'{e.text}' can never be satisfied — every possible "
                    f"state violates it, so this requirement always halts "
                    f"execution."
                ),
            ))
        elif status == "unknown":
            findings.append(_inconclusive("always_deny", [e.text]))
    return findings


def _check_dead_forbid(enc, entries, swallowed) -> list[Finding]:
    """Check 2 — a forbid whose effect (C ∧ ¬E) is UNSAT never fires.
    Suppressed for a statement check 4 already flagged (§9: run check 4
    first, report the more specific diagnosis, not both)."""
    findings = []
    for e in entries:
        if e.verb != "forbid" or e.index in swallowed:
            continue
        status, _ = _run_query(enc, [(e.effect, _tracked_name(e.index, e.verb))])
        if status == "unsat":
            findings.append(Finding(
                kind="dead_forbid", severity="warning", statements=[e.text],
                explanation=(
                    f"'{e.text}' can never trigger — no possible state "
                    f"satisfies its condition, so this prohibition never "
                    f"fires."
                ),
            ))
        elif status == "unknown":
            findings.append(_inconclusive("dead_forbid", [e.text]))
    return findings


def _check_require_forbid_conflict(enc, entries, capped) -> list[Finding]:
    """Check 3 — a require and a forbid whose allowed-spaces are jointly
    UNSAT can never both be satisfied."""
    if capped:
        return []
    findings = []
    requires = [e for e in entries if e.verb == "require"]
    forbids = [e for e in entries if e.verb == "forbid"]
    for r in requires:
        for f in forbids:
            status, _ = _run_query(enc, [
                (r.allowed, _tracked_name(r.index, r.verb)),
                (f.allowed, _tracked_name(f.index, f.verb)),
            ])
            if status == "unsat":
                findings.append(Finding(
                    kind="require_forbid_conflict", severity="error",
                    statements=[r.text, f.text],
                    explanation=(
                        f"'{r.text}' and '{f.text}' can never both hold — "
                        f"any state satisfying one violates the other."
                    ),
                ))
            elif status == "unknown":
                findings.append(
                    _inconclusive("require_forbid_conflict", [r.text, f.text])
                )
    return findings


def _check_unless_swallows_rule(enc, entries):
    """Check 4 — a statement whose own effect (given its own exception)
    is UNSAT reads as protection while providing none: the exception
    fires whenever the rule would. Highest-value finding in the
    taxonomy; runs before check 2 so its statement is suppressed there.
    Returns (findings, swallowed_indices)."""
    findings = []
    swallowed = set()
    for e in entries:
        if e.node.exception is None:
            continue
        status, _ = _run_query(enc, [(e.effect, _tracked_name(e.index, e.verb))])
        if status == "unsat":
            swallowed.add(e.index)
            findings.append(Finding(
                kind="unless_swallows_rule", severity="error", statements=[e.text],
                explanation=(
                    f"'{e.text}' can never fire — its own 'unless' exception "
                    f"holds in every state where the base condition does, so "
                    f"this rule can never actually enforce anything."
                ),
            ))
        elif status == "unknown":
            findings.append(_inconclusive("unless_swallows_rule", [e.text]))
    return findings, swallowed


def _check_redundant_forbid(enc, entries, capped) -> list[Finding]:
    """Check 5 — forbid_1 ∧ ¬forbid_2 UNSAT means forbid_1 is subsumed
    by forbid_2: whenever the narrower one would fire, the broader one
    already does."""
    if capped:
        return []
    findings = []
    forbids = [e for e in entries if e.verb == "forbid"]
    for e1 in forbids:
        for e2 in forbids:
            if e1.index == e2.index:
                continue
            status, _ = _run_query(enc, [
                (e1.effect, _tracked_name(e1.index, e1.verb)),
                (enc.z3.Not(e2.effect), f"not_{_tracked_name(e2.index, e2.verb)}"),
            ])
            if status == "unsat":
                findings.append(Finding(
                    kind="redundant_forbid", severity="warning",
                    statements=[e1.text, e2.text],
                    explanation=(
                        f"'{e1.text}' is redundant — whenever it would fire, "
                        f"'{e2.text}' already fires too."
                    ),
                ))
            elif status == "unknown":
                findings.append(
                    _inconclusive("redundant_forbid", [e1.text, e2.text])
                )
    return findings


def _check_dead_permit(enc, entries) -> list[Finding]:
    """Check 6 — a permit whose effect can't co-occur with the allowed
    space of every require/forbid can only ever apply to a state some
    other rule already blocks."""
    findings = []
    permits = [e for e in entries if e.verb == "permit"]
    if not permits:
        return findings
    guards = [e for e in entries if e.verb in ("require", "forbid")]
    for p in permits:
        tracked = [(p.effect, _tracked_name(p.index, p.verb))]
        tracked.extend((g.allowed, _tracked_name(g.index, g.verb)) for g in guards)
        status, _ = _run_query(enc, tracked)
        if status == "unsat":
            findings.append(Finding(
                kind="dead_permit", severity="warning", statements=[p.text],
                explanation=(
                    f"'{p.text}' can never actually apply — every state "
                    f"where it would grant permission is already blocked "
                    f"by another require/forbid rule."
                ),
            ))
        elif status == "unknown":
            findings.append(_inconclusive("dead_permit", [p.text]))
    return findings


def _check_constant_predicate(enc, statements) -> list[Finding]:
    """Check 7 — for each `define`, is its body a contradiction (always
    false) or a tautology (always true) for any possible subject?"""
    findings = []
    for stmt in _iter_statements(statements):
        if not isinstance(stmt, DefineNode):
            continue
        text = render(stmt)
        try:
            body_formula = enc.encode_predicate_body_standalone(
                stmt.name, stmt.condition
            )
        except UnencodableConstruct:
            findings.append(Finding(
                kind="inconclusive", severity="info", statements=[text],
                explanation=(
                    f"Couldn't determine a subject type for predicate "
                    f"'{stmt.name}' — check 7 (constant predicate) skipped "
                    f"for it."
                ),
            ))
            continue

        contradiction, _ = _run_query(
            enc, [(body_formula, f"predicate_{stmt.name}_body")]
        )
        if contradiction == "unsat":
            findings.append(Finding(
                kind="constant_predicate", severity="warning", statements=[text],
                explanation=f"'{text}' is always false — no subject can ever satisfy it.",
            ))
            continue
        if contradiction == "unknown":
            findings.append(_inconclusive("constant_predicate", [text]))
            continue

        tautology, _ = _run_query(
            enc, [(enc.z3.Not(body_formula), f"predicate_{stmt.name}_not_body")]
        )
        if tautology == "unsat":
            findings.append(Finding(
                kind="constant_predicate", severity="warning", statements=[text],
                explanation=f"'{text}' is always true — every subject satisfies it.",
            ))
        elif tautology == "unknown":
            findings.append(_inconclusive("constant_predicate", [text]))
    return findings


def check_agreement(statements, symbol_table) -> CheckResult:
    """Encode `statements` and run the seven core checks.

    Input mirrors analyzer.detect_contradictions(statements): a list of
    top-level statement ASTs. Never raises for out-of-fragment input —
    UnencodableConstruct (and any other encoding failure — invariant 8)
    is caught at this boundary and reported via
    CheckResult(encodable=False, skipped_reason=...) rather than a
    traceback or a false clean bill of health.
    """
    z3mod = _import_z3()
    start = time.monotonic()
    try:
        definitions = _build_definitions(statements)
        enc = _Encoder(z3mod, symbol_table, definitions)
        entries = _collect_deontic_entries(enc, statements)

        findings: list[Finding] = []
        cap = _cap_finding(len(entries))
        capped = cap is not None
        if cap is not None:
            findings.append(cap)

        unless_findings, swallowed = _check_unless_swallows_rule(enc, entries)
        findings.extend(unless_findings)
        findings.extend(_check_always_deny(enc, entries))
        findings.extend(_check_dead_forbid(enc, entries, swallowed))
        findings.extend(_check_require_forbid_conflict(enc, entries, capped))
        findings.extend(_check_redundant_forbid(enc, entries, capped))
        findings.extend(_check_dead_permit(enc, entries))
        findings.extend(_check_constant_predicate(enc, statements))
    except (UnencodableConstruct, NonlinearArithmetic) as exc:
        return CheckResult(
            findings=[], checked=0,
            elapsed_ms=(time.monotonic() - start) * 1000,
            encodable=False, skipped_reason=str(exc),
        )
    except Exception as exc:  # invariant 8 — never let anything escape
        return CheckResult(
            findings=[], checked=0,
            elapsed_ms=(time.monotonic() - start) * 1000,
            encodable=False, skipped_reason=f"{type(exc).__name__}: {exc}",
        )

    return CheckResult(
        findings=findings, checked=len(entries),
        elapsed_ms=(time.monotonic() - start) * 1000,
        encodable=True, skipped_reason=None,
    )


# ---------------------------------------------------------------------------
# check_source — static inspection from contract text (Halverson dry run,
# liminate-dev PR #89, product findings 1/2)
# ---------------------------------------------------------------------------

# The statement types check_agreement's seven checks need collected —
# every deontic verb (for the checks themselves), DefineNode (check 7),
# and RememberValueNode (value-position name inlining / TI-Q13). Anything
# else a line parses to (about, show, each, choose, ...) is discarded.
_CHECK_STATEMENT_TYPES = (
    RequireNode, ForbidNode, PermitNode, ExpectNode, RememberValueNode,
)


def _collect_checkable_statements(source: str) -> list:
    """Best-effort pre-pass collecting the top-level statement ASTs
    check_agreement needs from raw contract text: every `define`,
    `require`, `forbid`, `permit`, `expect`, and value-form `remember`
    line at indent 0.

    Deliberately NOT a thin wrapper around run._collect_deontic_statements
    — reusing that collector as-is silently breaks two of check_agreement's
    seven checks:

    1. `define` lines: run._collect_deontic_statements accumulates the
       name into a local predicate_names set (so later require/forbid
       applications parse correctly) and then `continue`s WITHOUT
       appending the DefineNode. check_agreement's check 7
       (_check_constant_predicate) iterates DefineNode from the statement
       list — a collector that drops it yields a silent zero-finding
       result for check 7, not an error.
    2. `remember ... with/from <value>` lines that parse to a
       RememberValueNode: _build_definitions scans the statement list for
       these to build the name -> defining-expression map that
       value-position name inlining (TI-Q13 closure) depends on. Without
       them, nonlinear arithmetic reached through a name (e.g. `remember
       a value called doubled from beta multiplied by beta`, then
       `forbid x is above doubled`) is silently never caught.

    run._collect_deontic_statements itself is untouched — its output feeds
    detect_contradictions in the live run() path, and changing what it
    returns would alter contradiction-detection behavior for every
    program. This is a deliberate duplicate of its scan structure, not a
    shared helper, for exactly that reason.

    Dispatches on the PARSED node's type, not the line's first token.
    `_parse_one_operation` (parser.py) consumes `starting "<date>"` and/or
    `until "<date>"` (TokenType.CONNECTIVE) and `inherited`
    (TokenType.OPERATOR) at statement-initial position, before the verb —
    so a first-token dispatch on TokenType.VERB silently drops every
    temporally-prefixed or `inherited`-prefixed statement (found via the
    Halverson re-run, liminate-dev PR #92: four statements across three
    documents excluded from every check, with encodable=True still
    reported — the headline result concealed the under-reporting).
    Parsing first and dispatching on the resulting AST type is the same
    pattern check_agreement itself already uses downstream, via
    _VERB_NAMES and _iter_statements.

    Anything that fails to tokenize/reorder/parse is silently skipped —
    this pass is advisory and must never introduce an error check_source's
    own run() call wouldn't also produce. Indented lines (when-block
    action lines) are excluded, matching the forward-declaration rule for
    predicate names run._collect_deontic_statements also follows.
    """
    statements: list = []
    predicate_names: set[str] = set()
    for line in source.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith("--"):
            continue
        try:
            if leading_indent(line) != 0:
                continue
            toks = tokenize(line)
        except LexError:
            continue
        if not toks:
            continue

        reordered = reorder(toks)
        if isinstance(reordered, LiminateResult):
            continue
        node = parse(reordered, predicate_names=predicate_names)
        if isinstance(node, LiminateResult):
            continue

        if isinstance(node, DefineNode):
            # Forward-declaration rule: a name enters predicate_names as
            # soon as its defining line is seen, before any later line
            # parses — order of accumulation must match a real program's
            # top-to-bottom read, unchanged from the prior implementation.
            predicate_names.add(node.name)
            statements.append(node)
        elif isinstance(node, _CHECK_STATEMENT_TYPES):
            statements.append(node)
    return statements


# ---------------------------------------------------------------------------
# check_source's type-inference pre-pass — unbound rule templates
# ---------------------------------------------------------------------------
#
# A Translate draft — and every shipped agreement template in
# liminate-dev's app/agreement_templates.py — is an *unbound rule
# template* by design: it references evidence fields (amount,
# manager-approval, ...) that no `remember` binds, so run()'s symbol table
# has no entry for them. _build_constants then allocates nothing for the
# missing name, and encode_field raises UnencodableConstruct the first
# time a condition actually touches it, so check_source reported
# encodable=False for every such template (Halverson dry run, liminate-dev
# PR #89, finding 1).
#
# This pass synthesizes type-only placeholder SymbolEntry objects
# (value=None — the Z3 encoder only reads the type, in _build_constants,
# to allocate a free constant) for referenced-but-unbound fields, inferred
# from how each field is used: a literal it's directly compared against,
# or, for `<subject> is <predicate>`, the predicate's own body. A field
# typed by neither path stays unresolved and still raises
# UnencodableConstruct at check time — that is invariant 8 working
# correctly, not a gap to paper over. A real `remember`/`define` binding
# always wins over an inferred placeholder (see the `name not in
# symbol_table` guard in check_source below).
#
# Ported from case-studies/halverson/check-output/check_harness.py in
# liminate-dev (the working prototype), adapted to checker.py's naming.
#
# Known limit: the heuristic below is exercised against the Halverson
# corpus's condition shapes only. FieldAccessNode on records, and the
# `within` / `includes` operators, were never hit by that corpus and are
# not covered here — a field reached only through one of those shapes
# stays unresolved. Generalizing beyond what that corpus proved is
# separate work.


def _condition_leaves(node):
    """Yield every ConditionNode/PredicateApplicationNode leaf inside a
    condition tree, descending CompoundConditionNode's and/or shape."""
    if isinstance(node, CompoundConditionNode):
        yield from _condition_leaves(node.left)
        yield from _condition_leaves(node.right)
    elif isinstance(node, (ConditionNode, PredicateApplicationNode)):
        yield node


def _literal_type(value_node) -> str | None:
    if isinstance(value_node, NumberLiteral):
        return "number"
    if isinstance(value_node, DateLiteral):
        return "date"
    if isinstance(value_node, (QuotedString, BareWord)):
        return "string"
    return None


def _predicate_subject_types(statements: list) -> dict[str, str]:
    """For each `define <name>: <condition>`, infer the scalar type a
    subject must have to be applied to it via `<subject> is <name>` —
    mirrors _Encoder._value_sort_hint / _infer_subject_sort (used by check
    7's standalone predicate-body encoding), but runs pre-encoding on raw
    ASTs rather than during Z3 constant allocation. E.g. `define large: is
    above 5000` implies a number subject."""
    subject_types: dict[str, str] = {}

    def hint(cond) -> str | None:
        if isinstance(cond, CompoundConditionNode):
            return hint(cond.left) or hint(cond.right)
        if isinstance(cond, ConditionNode) and isinstance(cond.field, EachPronoun):
            t = _literal_type(cond.value)
            if t is None and cond.value2 is not None:
                t = _literal_type(cond.value2)
            return t
        return None

    for stmt in statements:
        if isinstance(stmt, DefineNode):
            t = hint(stmt.condition)
            if t is not None:
                subject_types[stmt.name] = t
    return subject_types


_INFERABLE_DEONTIC_TYPES = (RequireNode, ForbidNode, PermitNode, ExpectNode)


def _infer_field_types(statements: list) -> dict[str, str]:
    """Walk every deontic condition, exception, and define body for a bare
    NameRef field and infer a scalar type — from the literal it's directly
    compared against, or, for a predicate application (`<subject> is
    <name>`), from the predicate's own body via `_predicate_subject_types`.
    First inference wins; a field typed by neither path is simply absent
    from the result and stays unresolved (raises UnencodableConstruct at
    check time, same as any other out-of-fragment reference)."""
    types: dict[str, str] = {}
    subject_types = _predicate_subject_types(statements)

    def note(name: str, scalar_type: str | None) -> None:
        if scalar_type is not None:
            types.setdefault(name, scalar_type)

    def walk_condition(cond) -> None:
        for leaf in _condition_leaves(cond):
            if isinstance(leaf, ConditionNode) and isinstance(leaf.field, NameRef):
                note(leaf.field.name, _literal_type(leaf.value))
                if leaf.value2 is not None:
                    note(leaf.field.name, _literal_type(leaf.value2))
            elif isinstance(leaf, PredicateApplicationNode) and isinstance(
                leaf.subject, NameRef
            ):
                note(leaf.subject.name, subject_types.get(leaf.predicate_name))

    for stmt in statements:
        if isinstance(stmt, DefineNode):
            walk_condition(stmt.condition)
        elif isinstance(stmt, _INFERABLE_DEONTIC_TYPES):
            walk_condition(stmt.condition)
            if stmt.exception is not None:
                walk_condition(stmt.exception)

    return types


def check_source(source: str, *, domain_packs=None) -> CheckResult:
    """Static inspection of contract text: check_agreement, wired up from
    source instead of hand-built statements + a symbol table.

    Runs `run(source, domain_packs=domain_packs, enter_phase2=False,
    auto_confirm_amber=True)` to populate a symbol table without entering
    Phase 2 (this is static inspection, not execution — no listener, no
    I/O) and without leaving an amber outcome unresolved. Collects the
    top-level define/require/forbid/permit/expect/remember statement ASTs
    from the same source text — see `_collect_checkable_statements`; in
    particular, `define` and value-form `remember` lines must both be
    collected, or check 7 and nonlinearity detection silently go inert.

    A contract source is very often an *unbound rule template* — it
    references evidence fields no `remember` in the source ever binds, so
    run()'s symbol table has no entry for them. Before handing off to
    check_agreement, this function adds a type-only placeholder
    SymbolEntry (see `_infer_field_types`) for every referenced-but-unbound
    field it can infer a scalar type for; a real binding from `run()`
    always takes precedence. A field neither bound nor inferable is left
    alone and still surfaces as `encodable=False` from check_agreement's
    own UnencodableConstruct boundary.

    Hands the (possibly widened) symbol table and the collected statements
    to `check_agreement` and returns its `CheckResult` unchanged — no
    wrapping, no extra fields. A caller that also needs the real symbol
    table calls `run()` directly instead.

    Never catches `CheckerUnavailable` — it propagates exactly as
    `check_agreement` raises it (z3 not installed). An out-of-fragment
    program is not an error either: `check_agreement` reports it as
    `CheckResult(encodable=False, skipped_reason=...)`, passed through
    unchanged. A program that fails to parse entirely collects zero
    statements and reports `checked=0` with no findings — also not an
    error; a caller wanting parse diagnostics should call `run()`.
    """
    contract_result = run(
        source,
        domain_packs=domain_packs,
        enter_phase2=False,
        auto_confirm_amber=True,
    )
    statements = _collect_checkable_statements(source)
    symbol_table = dict(contract_result.symbol_table)
    for name, scalar_type in _infer_field_types(statements).items():
        if name not in symbol_table:
            symbol_table[name] = SymbolEntry(name=name, value=None, type=scalar_type)
    return check_agreement(statements, symbol_table)

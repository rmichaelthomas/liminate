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


def check_agreement(statements, symbol_table) -> CheckResult:
    """Encode `statements` and run the seven core checks.

    Input mirrors analyzer.detect_contradictions(statements): a list of
    top-level statement ASTs. Never raises for out-of-fragment input —
    UnencodableConstruct is caught at this boundary and reported via
    CheckResult(encodable=False, skipped_reason=...).
    """
    _import_z3()
    raise NotImplementedError

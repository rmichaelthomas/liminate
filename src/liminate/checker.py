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

import time
from dataclasses import dataclass


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



def check_agreement(statements, symbol_table) -> CheckResult:
    """Encode `statements` and run the seven core checks.

    Input mirrors analyzer.detect_contradictions(statements): a list of
    top-level statement ASTs. Never raises for out-of-fragment input —
    UnencodableConstruct is caught at this boundary and reported via
    CheckResult(encodable=False, skipped_reason=...).
    """
    _import_z3()
    raise NotImplementedError

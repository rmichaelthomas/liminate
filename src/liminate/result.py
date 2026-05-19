"""Structured result objects returned by every interpreter call.

Sources:
- v1c §50 (five outcome taxonomy)
- v1d §64 (interpreter never calls input/print; CLI wraps display & prompts)
- v3a §122 (listener-mode result interface — four new statuses
  + structured metadata; the five-outcome taxonomy is extended by
  ERROR_RUNTIME for listener-specific failures)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResultStatus(Enum):
    SUCCESS = "success"
    AMBER_PRECEDENCE = "amber_precedence"   # v1a §30: mixed and/or in where
    AMBER_AMBIGUITY = "amber_ambiguity"     # inception §17: reorderer ambiguity
    ERROR_PARSE = "error_parse"             # v1c §50 outcome 4
    ERROR_SEMANTIC = "error_semantic"       # v1c §50 outcome 5
    # v3a §122 — listener-mode statuses. LISTENING is yielded once when
    # Phase 2 begins. HANDLER_FIRE wraps every action-block statement
    # result with trigger metadata. SHUTDOWN is the terminal result.
    # ERROR_RUNTIME covers cycle detection (§114), adapter failure
    # (§120), and adapter type mismatches (§116).
    LISTENING = "listening"
    HANDLER_FIRE = "handler_fire"
    SHUTDOWN = "shutdown"
    ERROR_RUNTIME = "error_runtime"
    # Normative Era batch 2: a `require` condition evaluated false at
    # runtime. Distinct from ERROR_SEMANTIC ("the program has a bug")
    # — REQUIREMENT_NOT_MET means "the data violates a rule."
    REQUIREMENT_NOT_MET = "requirement_not_met"


@dataclass
class LiminateResult:
    status: ResultStatus
    canonical: str | None = None
    output: list[str] | None = None
    message: str | None = None
    executed: bool = False
    # `pending_ast` carries the parsed-but-not-executed AST through an amber
    # outcome so the CLI wrapper can resume after user confirmation
    # (v1d §64: two-step flow keeps the core interpreter stateless).
    pending_ast: Any = field(default=None, repr=False)
    # v3a §122 — structured metadata for listener-mode results:
    #   LISTENING: {"watching": [name, ...]}
    #   HANDLER_FIRE: {"trigger": {"source", "handler_index",
    #                              "values_changed", "new_values"}}
    #   SHUTDOWN: {"reason": "finish"|"adapter_complete"|"external"|
    #                        "no_adapters"|"error",
    #              "handler_index": <int, optional>}
    #   ERROR_RUNTIME: {"kind": "cycle"|"adapter_failure"|"type_mismatch",
    #                   ...}
    # None for Phase 1 results (v2d-identical contract preserved).
    metadata: dict | None = None

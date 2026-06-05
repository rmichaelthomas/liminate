"""Phase 3 §A0 benchmark harness — regression baseline for the four
existing pack-verb execution types that the iterable-pack-verb refactor
threads `current_item` through.

Exercises:
  B1 cite pass            -> substring_check  -> SUCCESS
  B2 cite fail            -> substring_check  -> PACK_VERB_FAILURE substring_not_found
  B3 verify mismatch      -> compare_values   -> PACK_VERB_FAILURE comparison_mismatch
  B4 measure out of tol   -> numeric_extract  -> PACK_VERB_FAILURE outside_tolerance
  B5 validate range diff  -> range_check      -> PACK_VERB_FAILURE range_mismatch

Run from the repo root:  python3 benchmarks/_phase3_interpreter_bench.py
Output is deterministic Markdown written to stdout.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from liminate.adapter import TestDomainPack, parse_pack_verb_signature  # noqa: E402
from liminate.vocabulary import deactivate_all_pack_words  # noqa: E402

from tests._v3a_helpers import run_v3a  # noqa: E402


def _bench_pack() -> TestDomainPack:
    """cite / verify / measure / validate over substring_check,
    compare_values, numeric_extract_compare, range_check."""
    vocab = [("claim", "noun"), ("source", "noun"), ("window", "noun")]
    verbs = [
        parse_pack_verb_signature({
            "word": "cite",
            "slots": [
                {"name": "text", "connective": None, "required": True,
                 "value_type": "value"},
                {"name": "source", "connective": "from", "required": True,
                 "value_type": "name", "type_constraint": "source"},
            ],
            "execution": {"type": "substring_check",
                          "check_slot": "text", "against_slot": "source"},
        }),
        parse_pack_verb_signature({
            "word": "verify",
            "slots": [
                {"name": "claim", "connective": None, "required": True,
                 "value_type": "name", "type_constraint": "claim"},
                {"name": "source", "connective": "from", "required": True,
                 "value_type": "name", "type_constraint": "source"},
            ],
            "execution": {"type": "compare_values",
                          "left_slot": "claim", "right_slot": "source",
                          "comparison": "structural", "on_mismatch": "flag",
                          "status_target": "verification-status",
                          "details_target": "verification-divergences"},
        }),
        parse_pack_verb_signature({
            "word": "measure",
            "slots": [
                {"name": "value", "connective": None, "required": True,
                 "value_type": "value"},
                {"name": "source", "connective": "from", "required": True,
                 "value_type": "name", "type_constraint": "source"},
                {"name": "tolerance", "connective": "within", "required": True,
                 "value_type": "value"},
            ],
            "execution": {"type": "numeric_extract_compare",
                          "check_slot": "value", "against_slot": "source",
                          "tolerance_slot": "tolerance", "on_mismatch": "flag",
                          "status_target": "measure-status",
                          "matched_target": "measure-matched",
                          "delta_target": "measure-delta"},
        }),
        parse_pack_verb_signature({
            "word": "validate",
            "slots": [
                {"name": "claimed", "connective": None, "required": True,
                 "value_type": "value"},
                {"name": "reference", "connective": "from", "required": True,
                 "value_type": "name", "type_constraint": "window"},
            ],
            "execution": {"type": "range_check",
                          "check_slot": "claimed", "against_slot": "reference",
                          "on_mismatch": "flag",
                          "status_target": "range-status",
                          "claimed_target": "range-claimed",
                          "reference_target": "range-reference",
                          "divergence_target": "range-divergence"},
        }),
    ]
    return TestDomainPack(declarations=[], script=[], name="bench",
                          vocabulary=vocab, verbs=verbs)


CASES = [
    ("B1", "cite pass", '''
        remember a source called the-source with "revenue was 100"
        cite "revenue" from the-source
    '''),
    ("B2", "cite fail", '''
        remember a source called the-source with "revenue was 100"
        cite "deficit" from the-source
    '''),
    ("B3", "verify structural mismatch", '''
        remember a claim called the-claim with customer as "acme" and total as 100
        remember a source called the-source with customer as "acme" and total as 200
        verify the-claim from the-source
    '''),
    ("B4", "measure outside tolerance", '''
        remember a source called the-source with "the closest figure is 150"
        measure 100 from the-source within 1
    '''),
    ("B5", "validate range mismatch", '''
        remember a window called the-window with "between 10 and 20"
        validate "from 10 to 25" from the-window
    '''),
]


def run() -> str:
    lines = ["# Phase 3 Interpreter Benchmark — existing pack verbs",
             "",
             "Regression baseline for cite/verify/measure/validate. Each case "
             "records the final pack-verb result's status, failure_type, and "
             "message.", ""]
    for cid, label, src in CASES:
        deactivate_all_pack_words()
        _, results = run_v3a(src, pack=_bench_pack())
        last = results[-1]
        meta = last.metadata or {}
        ftype = meta.get("failure_type", "—")
        lines.append(f"## {cid} — {label}")
        lines.append(f"- status: `{last.status.name}`")
        lines.append(f"- failure_type: `{ftype}`")
        lines.append(f"- message: `{last.message or '—'}`")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.stdout.write(run())

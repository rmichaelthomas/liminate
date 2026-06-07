```json
{
  "source_repo": "priyaprabhupai/cobol-programs",
  "program": "swathi_cobolChallenge_22",
  "rule_summary": "Parenthesized COMPUTE expression for ws-ticket needs explicit arithmetic fidelity review.",
  "expressibility": "pack-needed",
  "pack_needed": "decimal-scale",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE WS-TICKET = ( WS-PRICE * 20 ) / 100",
      "limn": "not expressed in base vocabulary",
      "risk": "decimal-scale semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE WS-TICKET = ( WS-PRICE * 20 ) / 100`
Duplicate count collapsed into this rule: 0.
Fidelity surface: because "decimal-scale semantics are material to the COBOL rule"
Pack-needed rationale: Parenthesized COMPUTE expression for ws-ticket needs explicit arithmetic fidelity review.

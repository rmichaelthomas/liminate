```json
{
  "source_repo": "ignamiguel/fiuba-algoritmos-4-cobol",
  "program": "credit_card-sample-full",
  "rule_summary": "Parenthesized COMPUTE expression for ws-total-amount needs explicit arithmetic fidelity review.",
  "expressibility": "pack-needed",
  "pack_needed": "decimal-scale",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE WS-total-amount = (WS-total-amount + WS-C1-IMPORTE)",
      "limn": "not expressed in base vocabulary",
      "risk": "decimal-scale semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE WS-total-amount = (WS-total-amount + WS-C1-IMPORTE)`
Duplicate count collapsed into this rule: 2.
Fidelity surface: because "decimal-scale semantics are material to the COBOL rule"
Pack-needed rationale: Parenthesized COMPUTE expression for ws-total-amount needs explicit arithmetic fidelity review.

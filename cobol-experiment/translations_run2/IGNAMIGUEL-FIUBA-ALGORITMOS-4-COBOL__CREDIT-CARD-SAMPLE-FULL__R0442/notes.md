```json
{
  "source_repo": "ignamiguel/fiuba-algoritmos-4-cobol",
  "program": "credit_card-sample-full",
  "rule_summary": "COBOL intrinsic or exponentiation expression requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "COMPUTE WS-C1-IMPORTE = FUNCTION NUMVAL(WS-C1-IMPORTE)",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE WS-C1-IMPORTE = FUNCTION NUMVAL(WS-C1-IMPORTE)`
Duplicate count collapsed into this rule: 2.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

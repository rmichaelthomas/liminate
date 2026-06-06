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
      "cobol": "COMPUTE WS-Saldo-amount = FUNCTION NUMVAL(WS-Saldo-amount)",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE WS-Saldo-amount = FUNCTION NUMVAL(WS-Saldo-amount)`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

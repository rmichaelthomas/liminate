```json
{
  "source_repo": "lucasrmagalhaes/learning-COBOL",
  "program": "PROGCOB07",
  "rule_summary": "Parenthesized COMPUTE expression for wrk-media needs explicit arithmetic fidelity review.",
  "expressibility": "pack-needed",
  "pack_needed": "decimal-scale",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE WRK-MEDIA = (WRK-NOTA1 + WRK-NOTA2) / 2.",
      "limn": "not expressed in base vocabulary",
      "risk": "decimal-scale semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE WRK-MEDIA = (WRK-NOTA1 + WRK-NOTA2) / 2.`
Duplicate count collapsed into this rule: 0.
Fidelity surface: because "decimal-scale semantics are material to the COBOL rule"
Pack-needed rationale: Parenthesized COMPUTE expression for wrk-media needs explicit arithmetic fidelity review.

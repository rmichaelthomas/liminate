```json
{
  "source_repo": "lucasrmagalhaes/learning-COBOL",
  "program": "PROGCOB11",
  "rule_summary": "Parenthesized COMPUTE expression for wrk-area needs explicit arithmetic fidelity review.",
  "expressibility": "pack-needed",
  "pack_needed": "decimal-scale",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE WRK-AREA = (WRK-LARGURA * WRK-COMPRIMENTO)",
      "limn": "not expressed in base vocabulary",
      "risk": "decimal-scale semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE WRK-AREA = (WRK-LARGURA * WRK-COMPRIMENTO)`
Duplicate count collapsed into this rule: 0.
Fidelity surface: because "decimal-scale semantics are material to the COBOL rule"
Pack-needed rationale: Parenthesized COMPUTE expression for wrk-area needs explicit arithmetic fidelity review.

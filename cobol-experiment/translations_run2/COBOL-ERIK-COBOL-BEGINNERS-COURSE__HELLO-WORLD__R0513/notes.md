```json
{
  "source_repo": "COBOL-Erik/COBOL-Beginners-Course",
  "program": "HELLO-WORLD",
  "rule_summary": "Parenthesized COMPUTE expression for y needs explicit arithmetic fidelity review.",
  "expressibility": "pack-needed",
  "pack_needed": "decimal-scale",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE Y = (((X + 1) - 1) * 6) / 3",
      "limn": "not expressed in base vocabulary",
      "risk": "decimal-scale semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE Y = (((X + 1) - 1) * 6) / 3`
Duplicate count collapsed into this rule: 0.
Fidelity surface: because "decimal-scale semantics are material to the COBOL rule"
Pack-needed rationale: Parenthesized COMPUTE expression for y needs explicit arithmetic fidelity review.

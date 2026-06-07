```json
{
  "source_repo": "Martinfx/Cobol",
  "program": "RandomNumbers",
  "rule_summary": "COBOL intrinsic or exponentiation expression requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "COMPUTE W-RESULT = (FUNCTION RANDOM * 100) + 1",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE W-RESULT = (FUNCTION RANDOM * 100) + 1`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

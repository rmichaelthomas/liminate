```json
{
  "source_repo": "pyQode/pyqode.cobol",
  "program": "cobjapi",
  "rule_summary": "COBOL intrinsic or exponentiation expression requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "FUNCTION ALL INTRINSIC.",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `FUNCTION ALL INTRINSIC.`
Duplicate count collapsed into this rule: 6.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

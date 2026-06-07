```json
{
  "source_repo": "eugyenoch/cobol",
  "program": "employee-salary",
  "rule_summary": "COBOL intrinsic or exponentiation expression requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "DISPLAY \u201c**********************************\u201d AT 0622",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `DISPLAY “**********************************” AT 0622`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

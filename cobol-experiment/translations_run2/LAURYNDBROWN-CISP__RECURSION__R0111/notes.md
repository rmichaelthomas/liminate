```json
{
  "source_repo": "lauryndbrown/Cisp",
  "program": "recursion",
  "rule_summary": "COBOL intrinsic or exponentiation expression requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "MOVE \"RECURSION:INIT\" TO WS-LOG-RECORD-FUNCTION-NAME.",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `MOVE "RECURSION:INIT" TO WS-LOG-RECORD-FUNCTION-NAME.`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

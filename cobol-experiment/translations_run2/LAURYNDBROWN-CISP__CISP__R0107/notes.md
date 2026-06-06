```json
{
  "source_repo": "lauryndbrown/Cisp",
  "program": "cisp",
  "rule_summary": "COBOL intrinsic or exponentiation expression requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "02 WS-LOG-RECORD-FUNCTION-NAME PIC X(40).",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `02 WS-LOG-RECORD-FUNCTION-NAME PIC X(40).`
Duplicate count collapsed into this rule: 2.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

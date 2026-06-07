```json
{
  "source_repo": "JohnDovey/GNUCobol-Samples",
  "program": "GCic",
  "rule_summary": "COBOL intrinsic or exponentiation expression requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "GC0712 05 LINE 08 COL 39 VALUE '\"FUNCTION\" Is Optional '.",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `GC0712 05 LINE 08 COL 39 VALUE '"FUNCTION" Is Optional '.`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

```json
{
  "source_repo": "uwol/proleap-cobol-parser",
  "program": "SQ230A",
  "rule_summary": "COBOL intrinsic or exponentiation expression requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "- \"*****************************************\". SQ2304.2",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `- "*****************************************". SQ2304.2`
Duplicate count collapsed into this rule: 2.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

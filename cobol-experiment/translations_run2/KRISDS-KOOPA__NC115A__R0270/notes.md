```json
{
  "source_repo": "krisds/koopa",
  "program": "NC115A",
  "rule_summary": "COBOL intrinsic or exponentiation expression requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "DE-LETE. MOVE \"*****\" TO P-OR-F. ADD 1 TO DELETE-COUNTER. NC1154.2",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `DE-LETE. MOVE "*****" TO P-OR-F. ADD 1 TO DELETE-COUNTER. NC1154.2`
Duplicate count collapsed into this rule: 1.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

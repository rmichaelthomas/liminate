```json
{
  "source_repo": "sorenroug/COBOL-preservation",
  "program": "checkers",
  "rule_summary": "COBOL size-error overflow path requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "size-error-overflow",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "SUBTRACT V FROM Y GIVING ABS1 ON SIZE ERROR",
      "limn": "not expressed in base vocabulary",
      "risk": "size-error-overflow semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `SUBTRACT V FROM Y GIVING ABS1 ON SIZE ERROR`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL size-error overflow path requires a pack.

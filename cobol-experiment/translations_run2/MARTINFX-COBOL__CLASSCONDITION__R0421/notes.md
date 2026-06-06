```json
{
  "source_repo": "Martinfx/Cobol",
  "program": "ClassCondition",
  "rule_summary": "COBOL collation declaration requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "string-collation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "IF STR01 IS ALPHABETIC THEN",
      "limn": "not expressed in base vocabulary",
      "risk": "string-collation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF STR01 IS ALPHABETIC THEN`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL collation declaration requires a pack.

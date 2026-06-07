```json
{
  "source_repo": "derekjj/Mainframe-Dev",
  "program": "DCIA2PGC",
  "rule_summary": "String ordering or collation-sensitive comparison needs a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "string-collation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "IF ACCTNOL < 5 THEN",
      "limn": "not expressed in base vocabulary",
      "risk": "string-collation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF ACCTNOL < 5 THEN`
Duplicate count collapsed into this rule: 1.
Pack-needed rationale: String ordering or collation-sensitive comparison needs a pack.

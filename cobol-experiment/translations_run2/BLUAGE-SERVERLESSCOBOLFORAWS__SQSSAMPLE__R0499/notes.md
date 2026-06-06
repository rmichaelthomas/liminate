```json
{
  "source_repo": "BluAge/ServerlessCOBOLforAWS",
  "program": "SQSSAMPLE",
  "rule_summary": "String ordering or collation-sensitive comparison needs a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "string-collation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "IF ge-op-result >= 19 THEN",
      "limn": "not expressed in base vocabulary",
      "risk": "string-collation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF ge-op-result >= 19 THEN`
Duplicate count collapsed into this rule: 1.
Pack-needed rationale: String ordering or collation-sensitive comparison needs a pack.

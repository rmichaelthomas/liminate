```json
{
  "source_repo": "RegiBrazil/health-pipeline",
  "program": "HCMAPL01",
  "rule_summary": "String ordering or collation-sensitive comparison needs a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "string-collation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "IF CA-RETURN-CODE > 0",
      "limn": "not expressed in base vocabulary",
      "risk": "string-collation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF CA-RETURN-CODE > 0`
Duplicate count collapsed into this rule: 12.
Pack-needed rationale: String ordering or collation-sensitive comparison needs a pack.

```json
{
  "source_repo": "ronaldoottoni/Cobol",
  "program": "radiobtn",
  "rule_summary": "String ordering or collation-sensitive comparison needs a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "string-collation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "if radio-button-data >= 1 and <= 3",
      "limn": "not expressed in base vocabulary",
      "risk": "string-collation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `if radio-button-data >= 1 and <= 3`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: String ordering or collation-sensitive comparison needs a pack.

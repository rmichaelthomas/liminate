```json
{
  "source_repo": "nibrobb/1brc-cobol",
  "program": "1brc",
  "rule_summary": "String ordering or collation-sensitive comparison needs a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "string-collation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "IF MEAS-TEMP > WS-MEAS-MAX(WS-IDX) THEN",
      "limn": "not expressed in base vocabulary",
      "risk": "string-collation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF MEAS-TEMP > WS-MEAS-MAX(WS-IDX) THEN`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: String ordering or collation-sensitive comparison needs a pack.

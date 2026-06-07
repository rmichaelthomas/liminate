```json
{
  "source_repo": "zosconnect/zosconnect-sample-cobol-apirequester",
  "program": "imsclaim",
  "rule_summary": "COBOL substring predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "substring-predicate",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "BAQ-STATUS-MESSAGE(1:BAQ-STATUS-MESSAGE-LEN)",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `BAQ-STATUS-MESSAGE(1:BAQ-STATUS-MESSAGE-LEN)`
Duplicate count collapsed into this rule: 5.
Pack-needed rationale: COBOL substring predicate requires a pack.

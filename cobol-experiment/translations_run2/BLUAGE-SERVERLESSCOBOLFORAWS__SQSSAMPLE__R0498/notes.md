```json
{
  "source_repo": "BluAge/ServerlessCOBOLforAWS",
  "program": "SQSSAMPLE",
  "rule_summary": "COBOL substring predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "substring-predicate",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "msg-body-data(1:msg-body-len)",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `msg-body-data(1:msg-body-len)`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL substring predicate requires a pack.

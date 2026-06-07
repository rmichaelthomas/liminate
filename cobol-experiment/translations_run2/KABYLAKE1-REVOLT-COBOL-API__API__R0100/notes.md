```json
{
  "source_repo": "kabylake1/revolt-cobol-api",
  "program": "api",
  "rule_summary": "COBOL substring predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "substring-predicate",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "move low-value to ws-text(ws-count:1).",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `move low-value to ws-text(ws-count:1).`
Duplicate count collapsed into this rule: 2.
Pack-needed rationale: COBOL substring predicate requires a pack.

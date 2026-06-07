```json
{
  "source_repo": "JohnDovey/GNUCobol-Samples",
  "program": "GCic",
  "rule_summary": "COBOL substring predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "substring-predicate",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "GC0712 MOVE WS-Cmd-Args-TXT(WS-Cmd-SUB:1)",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `GC0712 MOVE WS-Cmd-Args-TXT(WS-Cmd-SUB:1)`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL substring predicate requires a pack.

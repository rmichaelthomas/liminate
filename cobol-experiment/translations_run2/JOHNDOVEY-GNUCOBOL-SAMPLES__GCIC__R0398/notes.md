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
      "cobol": "MOVE WHEN-COMPILED (1:12) TO WS-OC-Compile-DT",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `MOVE WHEN-COMPILED (1:12) TO WS-OC-Compile-DT`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL substring predicate requires a pack.

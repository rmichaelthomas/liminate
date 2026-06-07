```json
{
  "source_repo": "jnicholson/ITP-Advanced-COBOL-FINAL",
  "program": "G3-MAIN",
  "rule_summary": "COBOL screen/menu event routing requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "screen-event-routing",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "EVALUATE WS-SEL",
      "limn": "not expressed in base vocabulary",
      "risk": "screen-event-routing semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `EVALUATE WS-SEL`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL screen/menu event routing requires a pack.

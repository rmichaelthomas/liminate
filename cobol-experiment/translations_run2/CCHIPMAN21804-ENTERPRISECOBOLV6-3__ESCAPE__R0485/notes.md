```json
{
  "source_repo": "cchipman21804/EnterpriseCOBOLv6.3",
  "program": "ESCAPE",
  "rule_summary": "COBOL date intrinsic requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "date-arithmetic",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "move function current-date to datetime",
      "limn": "not expressed in base vocabulary",
      "risk": "date-arithmetic semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `move function current-date to datetime`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL date intrinsic requires a pack.

```json
{
  "source_repo": "vendethiel/trying.cob",
  "program": "anagram",
  "rule_summary": "COBOL date intrinsic requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "date-arithmetic",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "move function lower-case(WS-CANDIDATE(LS-I)) to LS-LC",
      "limn": "not expressed in base vocabulary",
      "risk": "date-arithmetic semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `move function lower-case(WS-CANDIDATE(LS-I)) to LS-LC`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL date intrinsic requires a pack.

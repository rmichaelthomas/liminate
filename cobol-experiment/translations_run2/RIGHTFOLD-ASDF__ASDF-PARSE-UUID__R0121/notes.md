```json
{
  "source_repo": "rightfold/asdf",
  "program": "asdf-parse-uuid",
  "rule_summary": "calculates ws nibble",
  "expressibility": "untranslatable",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "COMPUTE ws-nibble = ws-nibble - ws-ord-a + 10",
      "limn": "interpreter rejected generated base translation",
      "risk": "the candidate was not counted as an accepted translation",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE ws-nibble = ws-nibble - ws-ord-a + 10`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: calculates ws nibble

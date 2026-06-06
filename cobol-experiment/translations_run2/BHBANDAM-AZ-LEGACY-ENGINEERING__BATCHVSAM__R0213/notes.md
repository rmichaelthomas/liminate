```json
{
  "source_repo": "bhbandam/AZ-Legacy-Engineering",
  "program": "BATCHVSAM",
  "rule_summary": "COBOL substring predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "substring-predicate",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "MOVE BOOKS-TITLE-TEXT(77:77) TO OP-TITLE 02960000",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `MOVE BOOKS-TITLE-TEXT(77:77) TO OP-TITLE 02960000`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL substring predicate requires a pack.

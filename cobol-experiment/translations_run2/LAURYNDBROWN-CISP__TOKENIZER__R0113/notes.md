```json
{
  "source_repo": "lauryndbrown/Cisp",
  "program": "tokenizer",
  "rule_summary": "COBOL substring predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "substring-predicate",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "IF LS-SYMBOL(WS-COUNT)(WS-PARSE-STR-INDEX:1) = \" \" THEN",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF LS-SYMBOL(WS-COUNT)(WS-PARSE-STR-INDEX:1) = " " THEN`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL substring predicate requires a pack.

```json
{
  "source_repo": "RegiBrazil/DemoHealthCare",
  "program": "HCIVDB01",
  "rule_summary": "COBOL substring predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "substring-predicate",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "MOVE '00000' TO DB2-TIMESTAMP(22:5)",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `MOVE '00000' TO DB2-TIMESTAMP(22:5)`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL substring predicate requires a pack.

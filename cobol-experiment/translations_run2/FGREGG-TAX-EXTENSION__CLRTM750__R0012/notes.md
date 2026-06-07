```json
{
  "source_repo": "fgregg/tax_extension",
  "program": "CLRTM750",
  "rule_summary": "COBOL substring predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "substring-predicate",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "00245 STRING ACPT-DATE(5:2) '/' ACPT-DATE(7:2) '/' ACPT-DATE(3:2)",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `00245 STRING ACPT-DATE(5:2) '/' ACPT-DATE(7:2) '/' ACPT-DATE(3:2)`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL substring predicate requires a pack.

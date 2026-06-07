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
      "cobol": "00244 MOVE FUNCTION CURRENT-DATE(1:8) TO ACPT-DATE.",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `00244 MOVE FUNCTION CURRENT-DATE(1:8) TO ACPT-DATE.`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL substring predicate requires a pack.

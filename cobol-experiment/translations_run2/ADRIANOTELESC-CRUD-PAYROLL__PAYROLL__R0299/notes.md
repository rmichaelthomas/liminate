```json
{
  "source_repo": "adrianotelesc/crud-payroll",
  "program": "payroll",
  "rule_summary": "COBOL collation declaration requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "string-collation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "OR FS-NOME = SPACES OR FS-NOME IS NOT ALPHABETIC OR",
      "limn": "not expressed in base vocabulary",
      "risk": "string-collation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `OR FS-NOME = SPACES OR FS-NOME IS NOT ALPHABETIC OR`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL collation declaration requires a pack.

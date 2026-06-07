```json
{
  "source_repo": "morecobol/icu4c-cobol-samples",
  "program": "icu-Norm",
  "rule_summary": "checks the file status flag predicate",
  "expressibility": "untranslatable",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "IF (File-Status-Flag = \"00\") Then",
      "limn": "interpreter rejected generated base translation",
      "risk": "the candidate was not counted as an accepted translation",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF (File-Status-Flag = "00") Then`
Duplicate count collapsed into this rule: 1.
Pack-needed rationale: checks the file status flag predicate

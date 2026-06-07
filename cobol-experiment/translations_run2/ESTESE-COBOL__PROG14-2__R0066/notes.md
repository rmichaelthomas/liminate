```json
{
  "source_repo": "EstesE/COBOL",
  "program": "PROG14-2",
  "rule_summary": "Rounded COBOL target arithmetic requires an explicit rounding pack.",
  "expressibility": "pack-needed",
  "pack_needed": "currency-rounding",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE PREV-SEM-GPA ROUNDED = GP-SM/CREDITS-SM",
      "limn": "not expressed in base vocabulary",
      "risk": "currency-rounding semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE PREV-SEM-GPA ROUNDED = GP-SM/CREDITS-SM`
Duplicate count collapsed into this rule: 0.
Fidelity surface: because "currency-rounding semantics are material to the COBOL rule"
Pack-needed rationale: Rounded COBOL target arithmetic requires an explicit rounding pack.

```json
{
  "source_repo": "fgregg/tax_extension",
  "program": "ASREA748",
  "rule_summary": "Rounded COBOL target arithmetic requires an explicit rounding pack.",
  "expressibility": "pack-needed",
  "pack_needed": "currency-rounding",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "00207 COMPUTE FA-FROZ-EQLZD ROUNDED =",
      "limn": "not expressed in base vocabulary",
      "risk": "currency-rounding semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `00207 COMPUTE FA-FROZ-EQLZD ROUNDED =`
Duplicate count collapsed into this rule: 0.
Fidelity surface: because "currency-rounding semantics are material to the COBOL rule"
Pack-needed rationale: Rounded COBOL target arithmetic requires an explicit rounding pack.

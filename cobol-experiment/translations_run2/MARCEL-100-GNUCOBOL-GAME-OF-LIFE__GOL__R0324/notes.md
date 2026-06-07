```json
{
  "source_repo": "marcel-100/gnucobol-game-of-life",
  "program": "gol",
  "rule_summary": "Rounded COBOL target arithmetic requires an explicit rounding pack.",
  "expressibility": "pack-needed",
  "pack_needed": "currency-rounding",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE cell_random ROUNDED = random_seed",
      "limn": "not expressed in base vocabulary",
      "risk": "currency-rounding semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE cell_random ROUNDED = random_seed`
Duplicate count collapsed into this rule: 0.
Fidelity surface: because "currency-rounding semantics are material to the COBOL rule"
Pack-needed rationale: Rounded COBOL target arithmetic requires an explicit rounding pack.

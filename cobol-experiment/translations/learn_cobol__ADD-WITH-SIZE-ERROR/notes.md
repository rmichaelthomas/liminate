```json
{
  "source_repo": "learn_cobol",
  "program": "ADD-WITH-SIZE-ERROR",
  "rule_summary": "adds values with rounded result and size-error branch",
  "expressibility": "pack-needed",
  "pack_needed": "rounded numeric target and size-error pack",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "ADD in-1 TO in-2 GIVING result-1 ROUNDED",
      "limn": "not expressed",
      "risk": "rounded target behavior must be explicit",
      "recorded_in_because": false
    },
    {
      "kind": "truncation",
      "cobol": "ON SIZE ERROR",
      "limn": "not expressed",
      "risk": "target overflow path cannot be modeled by base vocabulary",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

The addition is simple, but the isolable rule includes both rounding and an overflow branch. That belongs in a numeric target/size-error pack.

```json
{
  "source_repo": "learn_cobol",
  "program": "RETIREMENT-AGE",
  "rule_summary": "women retire at 60, men at 65",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "permit"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "age >= 60",
      "limn": "age is above 59",
      "risk": "inclusive-vs-exclusive; faithful for integer ages only",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "age >= 65",
      "limn": "age is above 64",
      "risk": "inclusive-vs-exclusive; faithful for integer ages only",
      "recorded_in_because": true
    },
    {
      "kind": "precedence",
      "cobol": "female AND age >= 60 OR male AND age >= 65",
      "limn": "two permit lines",
      "risk": "COBOL AND/OR grouping made explicit",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The COBOL hides gender meanings behind 88-level condition names and relies on operator precedence. The Liminate version expands both branches so the thresholds and grouping are visible.

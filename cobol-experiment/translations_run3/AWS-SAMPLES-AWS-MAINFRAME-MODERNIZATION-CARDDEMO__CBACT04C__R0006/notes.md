```json
{
  "source_repo": "aws-samples/aws-mainframe-modernization-carddemo",
  "program": "CBACT04C",
  "rule_summary": "Monthly interest is the transaction-category balance times the annual rate divided by 1200.",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "= ( TRAN-CAT-BAL * DIS-INT-RATE) / 1200",
      "limn": "remember a value called monthly-interest with category-balance multiplied by annual-rate divided by 1200",
      "risk": "interest formula has no ROUNDED keyword; generic decimal arithmetic",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

An interest calculation that looks like a rounding candidate but has no ROUNDED keyword — so it is tagged `none`, not `rounding`. This is exactly the generic-arithmetic case Run 2 mislabelled.

```json
{
  "source_repo": "aws-samples/aws-mainframe-modernization-carddemo",
  "program": "COBIL00C",
  "rule_summary": "A bill payment is refused when the account balance is zero or less (nothing to pay).",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "forbid",
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "IF ACCT-CURR-BAL <= ZEROS AND",
      "limn": "forbid account-balance is below 0.01",
      "risk": "<= 0 on a 2-decimal balance rendered via is-below 0.01 (scale-unit shift)",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The `<= 0` guard is inclusive of zero; on a 2-decimal field it renders as `is below 0.01`, a boundary event whose shift size is the decimal scale.

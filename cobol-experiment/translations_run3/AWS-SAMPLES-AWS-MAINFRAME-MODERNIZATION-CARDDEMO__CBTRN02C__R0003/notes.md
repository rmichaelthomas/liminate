```json
{
  "source_repo": "aws-samples/aws-mainframe-modernization-carddemo",
  "program": "CBTRN02C",
  "rule_summary": "A transaction of zero or more is posted as a credit; a negative amount is posted as a debit.",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "permit",
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "IF DALYTRAN-AMT >= 0",
      "limn": "permit transaction-amount is above -0.01",
      "risk": ">= 0 on a 2-decimal amount rendered via is-above -0.01 (scale-unit shift)",
      "recorded_in_because": true
    },
    {
      "kind": "sign",
      "cobol": "IF DALYTRAN-AMT >= 0",
      "limn": "permit transaction-amount is above -0.01 / permit transaction-amount is below 0",
      "risk": "the rule classifies by sign of the amount",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

Two-branch classification. The `>= 0` boundary on a 2-decimal currency field shifts by the scale unit (0.01), and the rule also turns on the amount's sign — so it carries both a boundary and a sign event.

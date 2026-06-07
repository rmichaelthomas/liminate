```json
{
  "source_repo": "aws-samples/aws-mainframe-modernization-carddemo",
  "program": "CBTRN02C",
  "rule_summary": "A transaction is refused as over-limit when the new balance would exceed the credit limit.",
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
      "cobol": "IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL",
      "limn": "forbid temp-balance is above credit-limit",
      "risk": ">= rendered via swapped strict is-above; equality must remain inside the limit",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The over-limit guard is a base rule. The COBOL `>=` is inclusive; swapping operands under a strict `forbid is above` preserves the inclusive boundary exactly, recorded as a boundary fidelity event.

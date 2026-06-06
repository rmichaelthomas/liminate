```json
{
  "source_repo": "learn_cobol",
  "program": "NET-PAY",
  "rule_summary": "subtracts tax and deductions from gross pay",
  "expressibility": "pack-needed",
  "pack_needed": "packed-decimal currency rounding and signed display-size pack",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "GIVING net-pay ROUNDED",
      "limn": "not expressed",
      "risk": "rounded signed display target must be preserved",
      "recorded_in_because": false
    },
    {
      "kind": "sign",
      "cobol": "PIC +999.99",
      "limn": "not expressed",
      "risk": "display sign behavior is part of the financial result",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

The subtraction formula is understandable, but the rule is about a signed packed-decimal result with size-error behavior. That needs a currency/display pack rather than a word-salad base translation.

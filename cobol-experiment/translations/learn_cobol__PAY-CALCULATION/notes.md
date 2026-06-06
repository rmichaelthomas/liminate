```json
{
  "source_repo": "learn_cobol",
  "program": "PAY-CALCULATION",
  "rule_summary": "overtime pay applies above 37.5 hours at 1.5 times rate",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember",
    "permit"
  ],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE pay ROUNDED",
      "limn": "remember total-pay with standard-pay plus overtime-pay",
      "risk": "base Liminate arithmetic does not declare COBOL rounding mode",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The overtime formula itself fits base Liminate. The audit risk is rounding: COBOL says ROUNDED, while this base translation can show the formula but not the exact target-picture rounding behavior.

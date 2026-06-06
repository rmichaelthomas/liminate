```json
{
  "source_repo": "learn_cobol",
  "program": "SHOPPING-BILL",
  "rule_summary": "adds item cost to running shopping bill",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "ADD item-cost TO total-bill ROUNDED",
      "limn": "total-bill plus item-cost",
      "risk": "base Liminate does not model rounded accumulation into the target field",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The running-total operation fits base Liminate. The risk is that COBOL rounds into the bill field after the add.

```json
{
  "source_repo": "learn_cobol",
  "program": "ELECTRICITY-BILL",
  "rule_summary": "reject negative usage and calculate tiered electricity charge",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember",
    "forbid",
    "permit"
  ],
  "fidelity_events": [
    {
      "kind": "sign",
      "cobol": "IF units NEGATIVE",
      "limn": "forbid units is below 0",
      "risk": "negative usage is treated as rejection",
      "recorded_in_because": true
    },
    {
      "kind": "rounding",
      "cobol": "COMPUTE charge ROUNDED",
      "limn": "remember charge with basic-charge plus extra-charge",
      "risk": "COBOL target rounding is not represented",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The core billing rule fits: negative consumption is forbidden and units above 72 move into a second rate. The base translation does not model target-field rounding or display formatting.

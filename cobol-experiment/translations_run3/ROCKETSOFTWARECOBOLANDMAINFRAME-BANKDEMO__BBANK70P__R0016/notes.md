```json
{
  "source_repo": "RocketSoftwareCOBOLandMainframe/BankDemo",
  "program": "BBANK70P",
  "rule_summary": "A loan term may not exceed 1200 months (100 years).",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "forbid",
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "IF WS-CALC-WORK-TERM-N IS GREATER THAN 1200",
      "limn": "forbid loan-term-months is above 1200",
      "risk": "strict > 1200 maps directly to is-above 1200; no inclusive boundary to shift",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

A strict `>` cap. Because the COBOL comparison is already strict, it maps directly to `is above` with no shift — tagged `none`, demonstrating that not every threshold is a boundary event.

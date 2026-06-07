```json
{
  "source_repo": "RocketSoftwareCOBOLandMainframe/BankDemo",
  "program": "BBANK70P",
  "rule_summary": "A loan interest rate of 100% or more is rejected as outrageous.",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "remember",
    "require"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "IF WS-CALC-WORK-PERC-N IS NOT LESS THAN 100.000",
      "limn": "require interest-rate is below 100",
      "risk": "inclusive >= 100 (NOT LESS THAN 100.000) rejection rendered via strict is-below 100",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

`NOT LESS THAN 100.000` is an inclusive `>= 100` rejection; the valid region `< 100` maps to `require is below 100` — a boundary event.

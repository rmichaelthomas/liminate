```json
{
  "source_repo": "RocketSoftwareCOBOLandMainframe/BankDemo",
  "program": "BBANK70P",
  "rule_summary": "A loan interest rate must be greater than zero.",
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
      "cobol": "IF WS-CALC-WORK-PERC-N IS NOT GREATER THAN ZERO",
      "limn": "require interest-rate is above 0",
      "risk": "inclusive <= 0 (NOT GREATER THAN ZERO) rejection rendered via strict is-above 0",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

`NOT GREATER THAN ZERO` is an inclusive `<= 0` rejection; the valid region `> 0` maps to `require is above 0`, recorded as a boundary event.

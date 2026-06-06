```json
{
  "source_repo": "learn_cobol",
  "program": "PAY-MODULAR-VERSION",
  "rule_summary": "modular version of overtime pay above 37.5 hours",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember",
    "permit"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "hours-worked <= 37.5",
      "limn": "hours-worked is below 37.51",
      "risk": "inclusive decimal boundary assumes PIC 99V99 centesimal precision",
      "recorded_in_because": true
    },
    {
      "kind": "rounding",
      "cobol": "COMPUTE pay ROUNDED",
      "limn": "remember regular-pay with hours-worked multiplied by rate-of-pay",
      "risk": "target-picture rounding not represented in base vocabulary",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

This is the same pay rule written in paragraphs. The non-overtime branch is expressible, but the decimal boundary and COBOL rounding are explicit audit events.

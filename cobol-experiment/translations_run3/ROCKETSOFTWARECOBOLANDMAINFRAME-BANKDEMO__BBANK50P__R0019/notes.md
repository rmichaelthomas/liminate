```json
{
  "source_repo": "RocketSoftwareCOBOLandMainframe/BankDemo",
  "program": "BBANK50P",
  "rule_summary": "Funds cannot be transferred out of an account that is already in negative balance.",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "forbid",
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "sign",
      "cobol": "IF WS-XFER-ACCT-FROM-BAL-N IS LESS THAN ZERO",
      "limn": "forbid from-balance is below 0",
      "risk": "strict < 0 negative-sign test mapped directly to is-below 0",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

A negative-balance block. The strict `< 0` is a direct map; the rule turns on the sign of the balance, so it is tagged `sign` with no boundary shift.

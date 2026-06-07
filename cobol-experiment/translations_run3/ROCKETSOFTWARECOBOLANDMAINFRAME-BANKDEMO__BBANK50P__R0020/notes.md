```json
{
  "source_repo": "RocketSoftwareCOBOLandMainframe/BankDemo",
  "program": "BBANK50P",
  "rule_summary": "A transfer amount may not exceed the available balance in the source account.",
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
      "cobol": "IF WS-XFER-AMT-NUM-N IS GREATER THAN WS-XFER-ACCT-FROM-BAL-N",
      "limn": "forbid transfer-amount is above from-balance",
      "risk": "strict > between two variables maps directly to is-above; no boundary shift",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

A clean strict comparison between two amounts — direct map to `is above`, tagged `none`.

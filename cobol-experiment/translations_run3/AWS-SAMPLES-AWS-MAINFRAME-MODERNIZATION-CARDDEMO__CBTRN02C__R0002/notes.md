```json
{
  "source_repo": "aws-samples/aws-mainframe-modernization-carddemo",
  "program": "CBTRN02C",
  "rule_summary": "The working balance is current cycle credit minus debit plus the new transaction amount.",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "COMPUTE WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT",
      "limn": "remember a value called temp-balance with current-cycle-credit minus current-cycle-debit plus transaction-amount",
      "risk": "plain COMPUTE without ROUNDED; arithmetic carries across directly",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

A clean arithmetic translation. Crucially the COMPUTE has no ROUNDED keyword, so this is tagged `none`, not `rounding` — the decontamination the corrected model requires.

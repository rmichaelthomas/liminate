```json
{
  "source_repo": "learn_cobol",
  "program": "INVESTIMENT",
  "rule_summary": "calculates investment interest and final amount with rounded packed fields",
  "expressibility": "pack-needed",
  "pack_needed": "packed-decimal rounded currency and size-error pack",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "GIVING temp ROUNDED / interest ROUNDED / amount-end-out ROUNDED",
      "limn": "not expressed",
      "risk": "multiple rounded targets affect the final amount",
      "recorded_in_because": false
    },
    {
      "kind": "truncation",
      "cobol": "ON SIZE ERROR",
      "limn": "not expressed",
      "risk": "overflow path cannot be expressed in base vocabulary",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

The interest formula is ordinary, but COBOL rounds at several intermediate fields and branches on size errors. Faithful translation needs a packed-decimal financial pack.

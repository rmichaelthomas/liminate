```json
{
  "source_repo": "ignamiguel/fiuba-algoritmos-4-cobol",
  "program": "credit_card-sample-full",
  "rule_summary": "calculates ws total amount",
  "expressibility": "untranslatable",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "COMPUTE WS-total-amount = WS-total-amount + WS-Saldo-amount",
      "limn": "interpreter rejected generated base translation",
      "risk": "the candidate was not counted as an accepted translation",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE WS-total-amount = WS-total-amount + WS-Saldo-amount`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: calculates ws total amount

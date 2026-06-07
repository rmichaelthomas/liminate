```json
{
  "source_repo": "learn_cobol",
  "program": "BALANCE",
  "rule_summary": "adds transaction amount to old balance",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "ADD amount, old-balance",
      "limn": "amount plus old-balance",
      "risk": "no special boundary or rounding decision in the isolated rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

This balance update fits cleanly in the base vocabulary. No special boundary or precedence decision is needed for the isolated addition.

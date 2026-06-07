```json
{
  "source_repo": "javiertello/UnizarBank",
  "program": "TRANSFER",
  "rule_summary": "A transfer is rejected when the requested amount exceeds the account balance.",
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
      "cobol": "IF CANTOT > SALDOACT",
      "limn": "forbid amount is above balance",
      "risk": "strict > between amount and balance maps directly to is-above",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

A direct strict comparison — clean translation, tagged `none`.

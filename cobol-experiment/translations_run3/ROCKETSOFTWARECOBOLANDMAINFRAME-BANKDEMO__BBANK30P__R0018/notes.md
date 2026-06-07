```json
{
  "source_repo": "RocketSoftwareCOBOLandMainframe/BankDemo",
  "program": "BBANK30P",
  "rule_summary": "The monthly service charge steps down as the balance crosses 100000, 10000, 5000, 1000 and 0.",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "permit",
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "IF WS-SRV-BAL-N IS GREATER THAN WS-SRV-BAL5",
      "limn": "permit balance is above 100000",
      "risk": "strict GREATER THAN comparisons map directly to is-above; no boundary shift",
      "recorded_in_because": true
    },
    {
      "kind": "precedence",
      "cobol": "IF WS-SRV-BAL-N IS GREATER THAN WS-SRV-BAL5",
      "limn": "five ordered permit lines, highest threshold first",
      "risk": "the cascade of GOTO-on-match IF blocks is order-sensitive; rendered as ordered permits so the first matching tier wins",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

A five-tier charge cascade. Every COBOL comparison is a strict `GREATER THAN`, so all map directly to `is above` (none events, not boundary). The cascade's first-match ordering is the one judgment call, recorded as a precedence event.

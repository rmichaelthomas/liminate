```json
{
  "source_repo": "mortgagesample",
  "program": "EPSMPMT-VALIDATION",
  "rule_summary": "validates mortgage principal and interest before calculating monthly payment",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember",
    "require",
    "forbid"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "EPSPDATA-PRINCIPLE-DATA > 0",
      "limn": "principal-amount is above 0",
      "risk": "strict positive boundary is direct",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "EPSPDATA-PRINCIPLE-DATA > STATIC-MAXIMUM-PRINCIPLE",
      "limn": "forbid principal-amount is above maximum-principal",
      "risk": "strict maximum boundary is direct",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "EPSPDATA-QUOTED-INTEREST-RATE <= 0",
      "limn": "require quoted-interest-rate is above 0",
      "risk": "negative/zero interest rejection restated as positive requirement",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The mortgage validation thresholds fit base Liminate very well. The translation states each rejection condition as a readable requirement or prohibition.

```json
{
  "source_repo": "learn_cobol",
  "program": "COST",
  "rule_summary": "adds VAT and price to produce cost",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "ADD vat, price GIVING cost-out",
      "limn": "vat plus price",
      "risk": "no special fidelity event in the isolated arithmetic",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The VAT addition is directly expressible in base Liminate. This rule has no boundary, sign, or rounding event in the excerpt.

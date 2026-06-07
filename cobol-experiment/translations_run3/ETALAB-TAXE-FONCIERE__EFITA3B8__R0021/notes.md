```json
{
  "source_repo": "etalab/taxe-fonciere",
  "program": "EFITA3B8",
  "rule_summary": "The municipal property-tax share is the municipal base times the municipal rate over 100, rounded.",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE COTISB-COTICOM     ROUNDED =",
      "limn": "remember a value called municipal-tax with municipal-base multiplied by municipal-rate divided by 100",
      "risk": "COBOL applies ROUNDED to the euro; base arithmetic drops the half-up rounding step",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

A currency calculation with a literal ROUNDED keyword. The base translation expresses base*rate/100 but cannot apply the half-up rounding, so it emits a `rounding` event. The unmet need is currency-rounding/decimal-scale.

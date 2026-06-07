```json
{
  "source_repo": "fgregg/tax_extension",
  "program": "ASHMA839",
  "rule_summary": "The prior adjusted base is the prior base times the prior-year multiplier, rounded.",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE PREV-ADJ-BASE ROUNDED =",
      "limn": "remember a value called prior-adjusted-base with prior-base multiplied by prior-multiplier",
      "risk": "COBOL applies ROUNDED (half-up); base arithmetic has no rounding directive, so the rounding step is dropped",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

A genuine rounding case: the COMPUTE carries the literal ROUNDED keyword. The base translation expresses the product but cannot apply the half-up rounding, so it emits a `rounding` fidelity event.

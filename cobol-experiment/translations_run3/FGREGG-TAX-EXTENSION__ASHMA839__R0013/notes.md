```json
{
  "source_repo": "fgregg/tax_extension",
  "program": "ASHMA839",
  "rule_summary": "A prior adjusted base that comes out negative is floored to zero.",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "permit",
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "sign",
      "cobol": "IF PREV-ADJ-BASE < 0",
      "limn": "permit prior-adjusted-base is below 0",
      "risk": "strict < 0 negative-sign test mapped directly to is-below 0 (no boundary shift)",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

A negative-floor normalisation. The strict `< 0` is a direct map to `is below 0`, so this carries a `sign` event but no boundary shift.

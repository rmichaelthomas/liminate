```json
{
  "source_repo": "learn_cobol",
  "program": "TIME-AND-DATE",
  "rule_summary": "uses a 96 pivot to choose century for two-digit years",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember",
    "permit"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "date-in-yy < 96",
      "limn": "date-year is below 96",
      "risk": "strict less-than is direct",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "date-in-yy >= 96",
      "limn": "date-year is above 95",
      "risk": "else branch inclusive boundary made explicit for integer YY",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

This is a classic two-digit-year pivot rule. It fits base Liminate, but the century cutoff is exactly the kind of boundary an auditor would want surfaced.

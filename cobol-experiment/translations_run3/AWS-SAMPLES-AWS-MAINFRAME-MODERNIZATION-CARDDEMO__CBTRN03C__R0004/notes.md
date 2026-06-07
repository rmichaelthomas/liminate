```json
{
  "source_repo": "aws-samples/aws-mainframe-modernization-carddemo",
  "program": "CBTRN03C",
  "rule_summary": "A transaction is included in the report only if its processing date falls within the start and end dates.",
  "expressibility": "pack-needed",
  "pack_needed": "date-arithmetic",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [],
  "interpreter_accepted": false
}
```

The range test compares 10-character date strings with `>=` and `<=`. Liminate's `is above`/`is below` are numeric-only, so date-string ordering cannot be expressed in the base vocabulary; this needs a date-arithmetic pack. No fidelity events are emitted on an untranslated rule.

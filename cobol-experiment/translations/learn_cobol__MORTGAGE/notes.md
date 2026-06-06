```json
{
  "source_repo": "learn_cobol",
  "program": "MORTGAGE",
  "rule_summary": "computes yearly mortgage interest and ending balance",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "PIC 9(6)V99 targets",
      "limn": "unbounded base values",
      "risk": "base Liminate does not enforce COBOL target picture size or decimal scale",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The annual mortgage arithmetic is readable in base Liminate. The missing fidelity is COBOL picture enforcement: the base language does not constrain the value to the original field size or scale.

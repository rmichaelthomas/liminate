```json
{
  "source_repo": "learn_cobol",
  "program": "ADDAMT",
  "rule_summary": "sums three input amounts",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "ADD AMT1-IN AMT2-IN AMT3-IN",
      "limn": "amount-one plus amount-two plus amount-three",
      "risk": "no special fidelity event in the isolated arithmetic",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The rule is a straight three-amount sum. It fits the base vocabulary without needing a domain pack.

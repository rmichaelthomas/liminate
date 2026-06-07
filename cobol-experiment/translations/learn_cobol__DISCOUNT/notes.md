```json
{
  "source_repo": "learn_cobol",
  "program": "DISCOUNT",
  "rule_summary": "subtracts discount from charge",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "GIVING discounted-charge ROUNDED",
      "limn": "discounted-charge with charge minus discount",
      "risk": "base Liminate does not declare COBOL rounded target-picture behavior",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The arithmetic is simple and expressible. The fidelity risk is not the subtraction; it is the COBOL rounded display target.

```json
{
  "source_repo": "RocketSoftwareCOBOLandMainframe/BankDemo",
  "program": "BBANK70P",
  "rule_summary": "The monthly loan payment is the standard amortization formula, rounded.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [],
  "interpreter_accepted": false
}
```

The amortization formula uses `**` exponentiation (raising one-plus-rate to the term). The base vocabulary has no exponentiation operator, so the rule cannot be expressed without a pack. Pack-needed (exponentiation); no fidelity events on an untranslated rule. (It also carries ROUNDED, but that is moot while the formula itself is inexpressible.)

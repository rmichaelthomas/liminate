```json
{
  "source_repo": "cobol-samples",
  "program": "COND88-CATEGORY",
  "rule_summary": "88-level category names map multiple literal values",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember",
    "permit"
  ],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "88 CATEGORY-A VALUE 'A', '3', '7'",
      "limn": "category-a-values includes category-code",
      "risk": "membership mapping is direct",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

This 88-level pattern maps cleanly to list membership. The Liminate reader does not need to chase the condition-name declaration.

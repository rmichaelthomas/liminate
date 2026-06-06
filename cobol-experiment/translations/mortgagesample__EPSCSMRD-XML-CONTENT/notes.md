```json
{
  "source_repo": "mortgagesample",
  "program": "EPSCSMRD-XML-CONTENT",
  "rule_summary": "builds XML/content buffers through low-level generated COBOL routines",
  "expressibility": "untranslatable",
  "pack_needed": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "generated buffer index and pointer arithmetic",
      "limn": "not expressed",
      "risk": "not an isolable business rule in human policy terms",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

This excerpt is generated-style buffer manipulation, not a human business rule. Even with a pack, translating it would test COBOL mechanics rather than Liminate's business-rule expressibility.

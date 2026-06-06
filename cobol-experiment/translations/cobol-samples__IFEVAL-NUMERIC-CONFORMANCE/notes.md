```json
{
  "source_repo": "cobol-samples",
  "program": "IFEVAL-NUMERIC-CONFORMANCE",
  "rule_summary": "checks whether a field is numeric before arithmetic",
  "expressibility": "pack-needed",
  "pack_needed": "numeric conformance predicate pack",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "IF NUMERIC-2 IS NUMERIC",
      "limn": "not expressed",
      "risk": "base vocabulary has no numeric-conformance predicate for storage fields",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

The business intent is clear: check numeric shape before arithmetic. Base Liminate has values, but not COBOL's `IS NUMERIC` storage-conformance test.

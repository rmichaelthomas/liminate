```json
{
  "source_repo": "rightfold/asdf",
  "program": "asdf-append-to-ledger",
  "rule_summary": "checks the fs type is predicate",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "forbid"
  ],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "direct predicate",
      "limn": "direct predicate",
      "risk": "no material fidelity event identified in this isolated rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

Source excerpt line: `IF fs-type IS NOT EQUAL TO 'D' AND 'P' THEN`
Duplicate count collapsed into this rule: 0.

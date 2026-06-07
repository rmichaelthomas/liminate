```json
{
  "source_repo": "devries/openfaas-cobol-template",
  "program": "handler",
  "rule_summary": "checks the stdin record predicate",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "permit"
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

Source excerpt line: `IF stdin-record = SPACE or stdin-record = LOW-VALUE THEN`
Duplicate count collapsed into this rule: 0.

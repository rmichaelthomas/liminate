```json
{
  "source_repo": "RegiBrazil/DemoHealthCare",
  "program": "HCAPDB02",
  "rule_summary": "checks the sqlcode predicate",
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

Source excerpt line: `IF SQLCODE NOT EQUAL 0`
Duplicate count collapsed into this rule: 1.

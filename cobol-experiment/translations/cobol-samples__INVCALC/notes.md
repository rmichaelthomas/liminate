```json
{
  "source_repo": "cobol-samples",
  "program": "INVCALC",
  "rule_summary": "calculates invoice line totals, taxable line tax, and cumulative invoice totals",
  "expressibility": "pack-needed",
  "pack_needed": "invoice line aggregation with currency scale and numeric conformance pack",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "INV-LINE-QUANTITY IS NUMERIC",
      "limn": "not expressed",
      "risk": "numeric conformance guard is missing",
      "recorded_in_because": false
    },
    {
      "kind": "rounding",
      "cobol": "packed decimal line totals and tax fields",
      "limn": "not expressed",
      "risk": "currency scale and tax precision affect totals",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

This is business logic, but it is table-driven aggregation over invoice lines with numeric validation and tax precision. That is exactly the sort of domain pack the experiment is meant to reveal.

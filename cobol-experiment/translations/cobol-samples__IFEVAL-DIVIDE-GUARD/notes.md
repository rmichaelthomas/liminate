```json
{
  "source_repo": "cobol-samples",
  "program": "IFEVAL-DIVIDE-GUARD",
  "rule_summary": "avoids divide-by-zero by requiring a divisor greater than zero",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember",
    "require"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "NUMERIC-1 IS GREATER THAN ZERO",
      "limn": "divisor is above 0",
      "risk": "strict positive boundary is direct",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

This is a validation rule to avoid divide-by-zero. It maps cleanly to `require divisor is above 0` before the division.

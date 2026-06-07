```json
{
  "source_repo": "learn_cobol",
  "program": "DIVIDE-NUMBER",
  "rule_summary": "divides a dividend by divisor and handles size errors",
  "expressibility": "pack-needed",
  "pack_needed": "decimal division with divide-by-zero and size-error pack",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "ON SIZE ERROR",
      "limn": "not expressed",
      "risk": "COBOL arithmetic exception path is not a base Liminate concept",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

A quotient can be written in base arithmetic, but this COBOL rule includes arithmetic exception handling. That exception contract is the missing domain behavior.

```json
{
  "source_repo": "learn_cobol",
  "program": "COMPOUND-INTEREST",
  "rule_summary": "computes compound interest with exponentiation and size-error handling",
  "expressibility": "pack-needed",
  "pack_needed": "financial exponentiation plus rounded currency overflow pack",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE amount-at-end ROUNDED",
      "limn": "not expressed",
      "risk": "target rounding and overflow are material",
      "recorded_in_because": false
    },
    {
      "kind": "type-coercion",
      "cobol": "** years",
      "limn": "not expressed",
      "risk": "base arithmetic contract does not include exponentiation",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

This is a real financial rule, but base Liminate lacks exponentiation and COBOL size-error semantics. It should be counted as pack demand, not forced into invalid syntax.

```json
{
  "source_repo": "learn_cobol",
  "program": "WORD-ORDER",
  "rule_summary": "chooses alphabetical order from a lexical comparison",
  "expressibility": "pack-needed",
  "pack_needed": "collation and string-order comparison pack",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "IF word-1 < word-2",
      "limn": "not expressed",
      "risk": "COBOL alphanumeric comparison depends on collating sequence",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

The rule depends on COBOL's alphanumeric ordering. Base Liminate has no explicit collation semantics, so a faithful translation needs a string-collation pack.

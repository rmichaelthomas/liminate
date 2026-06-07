```json
{
  "source_repo": "askadian/CobolJsonParser",
  "program": "JSONParser",
  "rule_summary": "COBOL numeric conformance predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "numeric-conformance",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "IF WS-TEMP-NUM IS NUMERIC THEN",
      "limn": "not expressed in base vocabulary",
      "risk": "numeric-conformance semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF WS-TEMP-NUM IS NUMERIC THEN`
Duplicate count collapsed into this rule: 3.
Pack-needed rationale: COBOL numeric conformance predicate requires a pack.

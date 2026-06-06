```json
{
  "source_repo": "rightfold/asdf",
  "program": "asdf-append-to-ledger",
  "rule_summary": "COBOL numeric conformance predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "numeric-conformance",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "IF FUNCTION TRIM(ws-amount) IS NUMERIC THEN",
      "limn": "not expressed in base vocabulary",
      "risk": "numeric-conformance semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF FUNCTION TRIM(ws-amount) IS NUMERIC THEN`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL numeric conformance predicate requires a pack.

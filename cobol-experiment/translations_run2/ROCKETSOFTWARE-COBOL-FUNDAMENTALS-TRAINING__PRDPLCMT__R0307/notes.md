```json
{
  "source_repo": "RocketSoftware/cobol-fundamentals-training",
  "program": "PRDPLCMT",
  "rule_summary": "COBOL numeric conformance predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "numeric-conformance",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "IF MY-VARIABLE IS NOT NUMERIC PRDPLCMT",
      "limn": "not expressed in base vocabulary",
      "risk": "numeric-conformance semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF MY-VARIABLE IS NOT NUMERIC PRDPLCMT`
Duplicate count collapsed into this rule: 1.
Pack-needed rationale: COBOL numeric conformance predicate requires a pack.

```json
{
  "source_repo": "kabylake1/revolt-cobol-api",
  "program": "api",
  "rule_summary": "COBOL substring predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "substring-predicate",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "if ls-token(1:1) is equal to space then",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `if ls-token(1:1) is equal to space then`
Duplicate count collapsed into this rule: 1.
Pack-needed rationale: COBOL substring predicate requires a pack.

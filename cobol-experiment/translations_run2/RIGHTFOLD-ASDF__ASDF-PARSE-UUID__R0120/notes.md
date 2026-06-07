```json
{
  "source_repo": "rightfold/asdf",
  "program": "asdf-parse-uuid",
  "rule_summary": "COBOL substring predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "substring-predicate",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "COMPUTE ws-nibble = FUNCTION ORD(ls-in(ws-j : 1)) - 1",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE ws-nibble = FUNCTION ORD(ls-in(ws-j : 1)) - 1`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL substring predicate requires a pack.

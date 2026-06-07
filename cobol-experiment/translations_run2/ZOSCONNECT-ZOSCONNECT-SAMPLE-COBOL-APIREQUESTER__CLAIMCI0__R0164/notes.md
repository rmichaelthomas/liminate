```json
{
  "source_repo": "zosconnect/zosconnect-sample-cobol-apirequester",
  "program": "claimci0",
  "rule_summary": "COBOL substring predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "substring-predicate",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "IF Xstatus2(1:Xstatus2-length) = 'Accepted'",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF Xstatus2(1:Xstatus2-length) = 'Accepted'`
Duplicate count collapsed into this rule: 1.
Pack-needed rationale: COBOL substring predicate requires a pack.

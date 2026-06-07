```json
{
  "source_repo": "cchipman21804/EnterpriseCOBOLv6.3",
  "program": "ESCAPE",
  "rule_summary": "COBOL numeric conformance predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "numeric-conformance",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "display \"Pursuers quantity is not numeric.\"",
      "limn": "not expressed in base vocabulary",
      "risk": "numeric-conformance semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `display "Pursuers quantity is not numeric."`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL numeric conformance predicate requires a pack.

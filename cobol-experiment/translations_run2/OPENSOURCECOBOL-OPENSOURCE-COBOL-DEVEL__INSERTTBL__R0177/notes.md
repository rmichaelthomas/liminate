```json
{
  "source_repo": "opensourcecobol/opensource-cobol-devel",
  "program": "INSERTTBL",
  "rule_summary": "COBOL intrinsic or exponentiation expression requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "DISPLAY \"*** SQL ERROR ***\".",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `DISPLAY "*** SQL ERROR ***".`
Duplicate count collapsed into this rule: 1.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

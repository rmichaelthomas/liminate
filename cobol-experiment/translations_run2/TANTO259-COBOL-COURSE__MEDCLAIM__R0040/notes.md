```json
{
  "source_repo": "tanto259/cobol-course",
  "program": "MEDCLAIM",
  "rule_summary": "COBOL date intrinsic requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "date-arithmetic",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "MOVE FUNCTION CURRENT-DATE TO HDR-CURRENT-DATE.",
      "limn": "not expressed in base vocabulary",
      "risk": "date-arithmetic semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `MOVE FUNCTION CURRENT-DATE TO HDR-CURRENT-DATE.`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL date intrinsic requires a pack.

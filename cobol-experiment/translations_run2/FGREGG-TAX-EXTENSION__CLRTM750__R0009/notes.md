```json
{
  "source_repo": "fgregg/tax_extension",
  "program": "CLRTM750",
  "rule_summary": "COBOL intrinsic or exponentiation expression requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "00088 10 ES-FUNCTION PIC 9 VALUE 0.",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `00088 10 ES-FUNCTION PIC 9 VALUE 0.`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

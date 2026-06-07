```json
{
  "source_repo": "RegiBrazil/DemoHealthCare",
  "program": "HCTRESTW",
  "rule_summary": "COBOL substring predicate requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "substring-predicate",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "truncation",
      "cobol": "MOVE HCPAPP-PATIENT-DETAILS(1:200) TO WS-TSQ-DATA",
      "limn": "not expressed in base vocabulary",
      "risk": "substring-predicate semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `MOVE HCPAPP-PATIENT-DETAILS(1:200) TO WS-TSQ-DATA`
Duplicate count collapsed into this rule: 5.
Pack-needed rationale: COBOL substring predicate requires a pack.

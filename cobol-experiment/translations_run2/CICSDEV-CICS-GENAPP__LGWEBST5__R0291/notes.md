```json
{
  "source_repo": "cicsdev/cics-genapp",
  "program": "lgwebst5",
  "rule_summary": "Parenthesized COMPUTE expression for ocountval needs explicit arithmetic fidelity review.",
  "expressibility": "pack-needed",
  "pack_needed": "decimal-scale",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "Compute OCountVal = (HHVal * 3600) +",
      "limn": "not expressed in base vocabulary",
      "risk": "decimal-scale semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `Compute OCountVal = (HHVal * 3600) +`
Duplicate count collapsed into this rule: 0.
Fidelity surface: because "decimal-scale semantics are material to the COBOL rule"
Pack-needed rationale: Parenthesized COMPUTE expression for ocountval needs explicit arithmetic fidelity review.

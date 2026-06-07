```json
{
  "source_repo": "adrianotelesc/crud-payroll",
  "program": "payroll",
  "rule_summary": "Parenthesized COMPUTE expression for fs-total-he needs explicit arithmetic fidelity review.",
  "expressibility": "pack-needed",
  "pack_needed": "decimal-scale",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE FS-TOTAL-HE = ( (FS-SALBA / FS-CH) + (FS-SALBA / FS-C",
      "limn": "not expressed in base vocabulary",
      "risk": "decimal-scale semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE FS-TOTAL-HE = ( (FS-SALBA / FS-CH) + (FS-SALBA / FS-C`
Duplicate count collapsed into this rule: 0.
Fidelity surface: because "decimal-scale semantics are material to the COBOL rule"
Pack-needed rationale: Parenthesized COMPUTE expression for fs-total-he needs explicit arithmetic fidelity review.

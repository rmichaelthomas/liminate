```json
{
  "source_repo": "adrianotelesc/crud-payroll",
  "program": "payroll",
  "rule_summary": "Parenthesized COMPUTE expression for fs-irrf needs explicit arithmetic fidelity review.",
  "expressibility": "pack-needed",
  "pack_needed": "decimal-scale",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "COMPUTE FS-IRRF = (((FS-SALBR - FS-INSS) - FS-TOTAL-DEP)",
      "limn": "not expressed in base vocabulary",
      "risk": "decimal-scale semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE FS-IRRF = (((FS-SALBR - FS-INSS) - FS-TOTAL-DEP)`
Duplicate count collapsed into this rule: 3.
Fidelity surface: because "decimal-scale semantics are material to the COBOL rule"
Pack-needed rationale: Parenthesized COMPUTE expression for fs-irrf needs explicit arithmetic fidelity review.

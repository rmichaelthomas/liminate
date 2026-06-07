```json
{
  "source_repo": "adrianotelesc/crud-payroll",
  "program": "payroll",
  "rule_summary": "Family allowance is paid per child at 41.37 for low salaries and 29.16 for a middle band.",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "permit",
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "WHEN FS-FILHOS > 0 AND FS-SALBA <= 806,80",
      "limn": "permit base-salary is below 806.81",
      "risk": "<= 806,80 rendered via is-below 806.81 (0.01 scale shift)",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "WHEN FS-SALBA > 806,81 AND FS-SALBA <= 1212,64 AND",
      "limn": "permit base-salary is below 1212.65",
      "risk": "<= 1212,64 rendered via is-below 1212.65",
      "recorded_in_because": true
    },
    {
      "kind": "precedence",
      "cobol": "WHEN FS-SALBA > 806,81 AND FS-SALBA <= 1212,64 AND",
      "limn": "permit base-salary is above 806.81 and base-salary is below 1212.65",
      "risk": "the WHEN combined three conditions with AND across a continuation line, split into explicit and-joined comparisons",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

A child-allowance eligibility rule. Two inclusive `<=` salary caps become scale-shifted boundary events, and the multi-line compound AND is made explicit (precedence).

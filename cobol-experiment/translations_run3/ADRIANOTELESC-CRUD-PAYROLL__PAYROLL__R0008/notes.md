```json
{
  "source_repo": "adrianotelesc/crud-payroll",
  "program": "payroll",
  "rule_summary": "INSS social-security is 8/9/11% by salary band, capped above the ceiling.",
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
      "cobol": "WHEN (FS-SALBR > 0) AND (FS-SALBR <= 1556,94)",
      "limn": "permit gross-salary is below 1556.95",
      "risk": "<= 1556,94 rendered via is-below 1556.95 (0.01 scale shift)",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "WHEN (FS-SALBR > 1556,94) AND (FS-SALBR <= 2594,92)",
      "limn": "permit gross-salary is below 2594.93",
      "risk": "<= 2594,92 rendered via is-below 2594.93",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "WHEN (FS-SALBR > 2594,92) AND (FS-SALBR <= 5189,82)",
      "limn": "permit gross-salary is below 5189.83",
      "risk": "<= 5189,82 rendered via is-below 5189.83",
      "recorded_in_because": true
    },
    {
      "kind": "precedence",
      "cobol": "WHEN (FS-SALBR > 0) AND (FS-SALBR <= 1556,94)",
      "limn": "permit gross-salary is above 0 and gross-salary is below 1556.95",
      "risk": "each EVALUATE WHEN was a compound (lower AND upper) bound, made explicit as two and-joined comparisons",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

A four-band tax bracket. Each band's inclusive `<=` upper bound shifts by the 0.01 currency scale (three boundary events), and the implicit AND of lower-and-upper bounds is made explicit (a precedence event). Note the source uses comma decimals, converted to dots.

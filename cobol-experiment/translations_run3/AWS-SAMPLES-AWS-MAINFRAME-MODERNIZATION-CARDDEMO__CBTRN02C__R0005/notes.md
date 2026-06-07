```json
{
  "source_repo": "aws-samples/aws-mainframe-modernization-carddemo",
  "program": "CBTRN02C",
  "rule_summary": "A transaction received after the account expiration date is refused.",
  "expressibility": "pack-needed",
  "pack_needed": "date-arithmetic",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [],
  "interpreter_accepted": false
}
```

`ACCT-EXPIRAION-DATE >= DALYTRAN-ORIG-TS(1:10)` is a date-string comparison; the base vocabulary compares only numbers. Pack-needed (date-arithmetic), empty fidelity.

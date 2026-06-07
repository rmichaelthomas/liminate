```json
{
  "source_repo": "learn_cobol",
  "program": "AGE-CHECK",
  "rule_summary": "classifies whether a person is over 21",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "permit"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "age <= 21",
      "limn": "age is below 22",
      "risk": "else branch made explicit; faithful for integer PIC 999 ages",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

This rule separates people over 21 from people 21 or younger. The COBOL only writes the greater-than branch; the else branch was made explicit and is faithful for integer ages.

```json
{
  "source_repo": "cobol-samples",
  "program": "NOTBOOL-FLAGS",
  "rule_summary": "pseudo-boolean conventions encode true values as T, Y, 1, or 88-level names",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember",
    "permit",
    "forbid"
  ],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "PIC X where T/Y/1/88-level values mean true",
      "limn": "literal equality permits",
      "risk": "literal conventions are direct once expanded",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The base vocabulary can hold legacy pseudo-boolean conventions once the magic values are named. The important translation step is to expose the convention, not to invent a boolean type.

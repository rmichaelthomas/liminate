```json
{
  "source_repo": "mortgagesample",
  "program": "EPSNBRVL-NUMBER-PARSER",
  "rule_summary": "validates numeric text by trimming spaces, allowing commas, and detecting decimal errors",
  "expressibility": "pack-needed",
  "pack_needed": "numeric text parsing and decimal-point validation pack",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "EPSPARM-VALIDATE-DATA(WS-IDX:1) IS NOT NUMERIC",
      "limn": "not expressed",
      "risk": "character-by-character numeric validation is outside base vocabulary",
      "recorded_in_because": false
    },
    {
      "kind": "boundary",
      "cobol": "UNTIL WS-IDX > WS-END-SPACE / < WS-LEADING-SPACES",
      "limn": "not expressed",
      "risk": "loop boundaries govern which characters are accepted",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

This routine is a validation rule over numeric text, not just plumbing. Faithful expression needs a parser-like pack for spaces, commas, decimals, and digit predicates.

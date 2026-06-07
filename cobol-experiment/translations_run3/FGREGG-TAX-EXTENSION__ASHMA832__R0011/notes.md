```json
{
  "source_repo": "fgregg/tax_extension",
  "program": "ASHMA832",
  "rule_summary": "Records must arrive in non-descending key order; an out-of-order key is a severe error.",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "forbid",
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "IF CUR-REC-KEY >= PREV-REC-KEY",
      "limn": "forbid current-key is below previous-key",
      "risk": ">= rendered via swapped strict is-below; equal keys must stay valid",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

Sequence validation. The inclusive `>=` between two keys becomes a swapped strict `forbid is below`, keeping equal keys valid — a boundary event with no scale loss.

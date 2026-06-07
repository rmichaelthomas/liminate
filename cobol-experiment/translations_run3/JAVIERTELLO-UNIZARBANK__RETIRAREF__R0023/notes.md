```json
{
  "source_repo": "javiertello/UnizarBank",
  "program": "RETIRAREF",
  "rule_summary": "A cash withdrawal is rejected when it exceeds the balance or is exactly zero.",
  "expressibility": "base",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [
    "forbid",
    "remember"
  ],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "IF REINTEGRO > SALDO OR REINTEGRO = 0.00",
      "limn": "forbid withdrawal is above balance / forbid withdrawal is 0.00",
      "risk": "the COBOL OR condition is split into two independent forbid statements so the disjunction is explicit",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

A compound `OR` rejection, split into two `forbid` statements so each arm is self-evident — recorded as a precedence event. Both arms are exact (strict `>` and equality).

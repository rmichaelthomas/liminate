```json
{
  "source_repo": "mortgagesample",
  "program": "EPSCMORT-SCREEN-FLOW",
  "rule_summary": "routes mortgage CICS screen flow by aid key and process indicator",
  "expressibility": "pack-needed",
  "pack_needed": "CICS mortgage screen-flow and DB2 state pack",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "EVALUATE TRUE with nested PROCESS-INDICATOR checks",
      "limn": "not expressed",
      "risk": "screen flow depends on CICS AID constants and process state",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

The rule is a screen-flow decision, but base Liminate has no CICS AID-key vocabulary or DB2-backed state model. A domain pack would make it expressible.

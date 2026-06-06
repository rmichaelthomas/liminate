```json
{
  "source_repo": "mortgagesample",
  "program": "EPSMLIST-CICS-NAVIGATION",
  "rule_summary": "routes CICS screen behavior by AID key and communication state",
  "expressibility": "pack-needed",
  "pack_needed": "CICS screen-event routing pack",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "EIBAID = DFHPF3 OR DFHPF12",
      "limn": "not expressed",
      "risk": "event-key routing semantics must preserve CICS constants",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

This is a UI routing rule rather than financial calculation. It is isolable, but it needs a CICS event/screen pack to be readable and faithful.

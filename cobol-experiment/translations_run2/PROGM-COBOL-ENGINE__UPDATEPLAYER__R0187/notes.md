```json
{
  "source_repo": "ProGM/COBOL-Engine",
  "program": "UpdatePlayer",
  "rule_summary": "calculates player pos y",
  "expressibility": "untranslatable",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "COMPUTE PLAYER-POS-Y = PLAYER-POS-Y + SPEED-Y * DELTA-TIME",
      "limn": "interpreter rejected generated base translation",
      "risk": "the candidate was not counted as an accepted translation",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `COMPUTE PLAYER-POS-Y = PLAYER-POS-Y + SPEED-Y * DELTA-TIME`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: calculates player pos y

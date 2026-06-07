```json
{
  "source_repo": "federico-priolo/GuiCOBOL",
  "program": "guicobol",
  "rule_summary": "checks the fine file predicate",
  "expressibility": "untranslatable",
  "pack_needed": null,
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "none",
      "cobol": "IF FINE-FILE = \"S\" GO TO EX-LETTURA.",
      "limn": "interpreter rejected generated base translation",
      "risk": "the candidate was not counted as an accepted translation",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF FINE-FILE = "S" GO TO EX-LETTURA.`
Duplicate count collapsed into this rule: 1.
Pack-needed rationale: checks the fine file predicate

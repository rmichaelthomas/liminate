```json
{
  "source_repo": "gaessaki/COBOLCalc",
  "program": "Window1.xaml",
  "rule_summary": "COBOL intrinsic or exponentiation expression requires a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "exponentiation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "set ws-lastInput = function numval(ls-temp) *>numval is an intristic function that allows us to cast a string into a number",
      "limn": "not expressed in base vocabulary",
      "risk": "exponentiation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `set ws-lastInput = function numval(ls-temp) *>numval is an intristic function that allows us to cast a string into a number`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: COBOL intrinsic or exponentiation expression requires a pack.

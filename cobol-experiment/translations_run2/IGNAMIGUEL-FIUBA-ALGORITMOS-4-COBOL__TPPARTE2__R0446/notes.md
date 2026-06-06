```json
{
  "source_repo": "ignamiguel/fiuba-algoritmos-4-cobol",
  "program": "tpparte2",
  "rule_summary": "String ordering or collation-sensitive comparison needs a pack.",
  "expressibility": "pack-needed",
  "pack_needed": "string-collation",
  "duplicate_of": null,
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "type-coercion",
      "cobol": "IF LINEA-A-ESCRIBIR > 60 THEN PERFORM SALTO-DE-PAGINA.",
      "limn": "not expressed in base vocabulary",
      "risk": "string-collation semantics are material to the COBOL rule",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": false
}
```

Source excerpt line: `IF LINEA-A-ESCRIBIR > 60 THEN PERFORM SALTO-DE-PAGINA.`
Duplicate count collapsed into this rule: 0.
Pack-needed rationale: String ordering or collation-sensitive comparison needs a pack.

```json
{
  "source_repo": "cobol-samples",
  "program": "IFEVAL-DUAL-EVALUATE",
  "rule_summary": "EVALUATE TRUE ALSO TRUE combines numeric comparison and string prefix checks",
  "expressibility": "pack-needed",
  "pack_needed": "substring/prefix predicate and multi-axis evaluate pack",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "precedence",
      "cobol": "EVALUATE TRUE ALSO TRUE",
      "limn": "not expressed",
      "risk": "multi-axis EVALUATE branch priority must be preserved",
      "recorded_in_because": false
    },
    {
      "kind": "type-coercion",
      "cobol": "ALPHA-1(1:3) EQUAL 'THX'",
      "limn": "not expressed",
      "risk": "base vocabulary lacks substring slicing",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

The branch logic combines two axes and substring predicates. A faithful readable translation needs a prefix/substring pack and explicit branch priority.

```json
{
  "source_repo": "cobol-samples",
  "program": "COND88-AGE-RANGES",
  "rule_summary": "88-level age names classify child through elderly ranges",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember",
    "permit"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "0 THRU 12",
      "limn": "person-age is above -1 and person-age is below 13",
      "risk": "inclusive integer range rewritten through strict operators",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "13 THRU 19",
      "limn": "person-age is above 12 and person-age is below 20",
      "risk": "inclusive integer range rewritten through strict operators",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "20 THRU 35",
      "limn": "person-age is above 19 and person-age is below 36",
      "risk": "inclusive integer range rewritten through strict operators",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "36 THRU 49",
      "limn": "person-age is above 35 and person-age is below 50",
      "risk": "inclusive integer range rewritten through strict operators",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "50 THRU 59",
      "limn": "person-age is above 49 and person-age is below 60",
      "risk": "inclusive integer range rewritten through strict operators",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "60 THRU 74",
      "limn": "person-age is above 59 and person-age is below 75",
      "risk": "inclusive integer range rewritten through strict operators",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "75 THRU 200",
      "limn": "person-age is above 74 and person-age is below 201",
      "risk": "inclusive integer range rewritten through strict operators",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The 88-level age bands are expressible, but every range boundary becomes visible. That is useful: the translation exposes exactly where an off-by-one error would occur.

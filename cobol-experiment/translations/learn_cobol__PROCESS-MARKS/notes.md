```json
{
  "source_repo": "learn_cobol",
  "program": "PROCESS-MARKS",
  "rule_summary": "classifies average marks into four bands",
  "expressibility": "base",
  "pack_needed": null,
  "verbs_used": [
    "remember",
    "permit"
  ],
  "fidelity_events": [
    {
      "kind": "boundary",
      "cobol": "40 THRU 49.9",
      "limn": "average-mark is above 39.9 and average-mark is below 50",
      "risk": "inclusive range rewritten through strict operators",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "50 THRU 59.9",
      "limn": "average-mark is above 49.9 and average-mark is below 60",
      "risk": "inclusive range rewritten through strict operators",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "60 THRU 69.9",
      "limn": "average-mark is above 59.9 and average-mark is below 70",
      "risk": "inclusive range rewritten through strict operators",
      "recorded_in_because": true
    },
    {
      "kind": "boundary",
      "cobol": "70 THRU 100",
      "limn": "average-mark is above 69.9 and average-mark is below 100.1",
      "risk": "upper boundary assumes one decimal place for the average",
      "recorded_in_because": true
    },
    {
      "kind": "precedence",
      "cobol": "(english-marks + math-marks) /2",
      "limn": "total-marks with english-marks plus math-marks; average-mark with total-marks divided by 2",
      "risk": "COBOL parentheses made explicit through an intermediate value",
      "recorded_in_because": true
    }
  ],
  "interpreter_accepted": true
}
```

The classification bands can be expressed, but every `THRU` range becomes an audit boundary. The average calculation also exposes a precedence concern because the COBOL uses parentheses.

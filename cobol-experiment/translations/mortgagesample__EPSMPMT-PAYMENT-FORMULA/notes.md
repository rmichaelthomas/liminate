```json
{
  "source_repo": "mortgagesample",
  "program": "EPSMPMT-PAYMENT-FORMULA",
  "rule_summary": "calculates amortized monthly payment using exponentiation",
  "expressibility": "pack-needed",
  "pack_needed": "mortgage amortization formula pack with exponentiation and decimal precision",
  "verbs_used": [],
  "fidelity_events": [
    {
      "kind": "rounding",
      "cobol": "EPSPDATA-RETURN-MONTH-PAYMENT target",
      "limn": "not expressed",
      "risk": "payment precision is financially material",
      "recorded_in_because": false
    },
    {
      "kind": "type-coercion",
      "cobol": "** WS-NUMBER-OF-MONTHS",
      "limn": "not expressed",
      "risk": "base vocabulary lacks exponentiation and amortization primitive",
      "recorded_in_because": false
    }
  ],
  "interpreter_accepted": false
}
```

The payment formula is central banking logic, but base Liminate cannot express exponentiation or the payment target's numeric precision. This is a strong pack-demand signal.

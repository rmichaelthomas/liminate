# Run 1 vs Run 2 Comparison

## Expressibility

|Outcome|Run 1 count|Run 1 %|Run 2 count|Run 2 %|
|---|---:|---:|---:|---:|
|base|18|56.2%|204|39.2%|
|pack-needed|13|40.6%|279|53.7%|
|untranslatable|1|3.1%|37|7.1%|

## Pack-demand ranking

|Run 1 top labels|Count|Run 2 top labels|Count|
|---|---:|---|---:|
|collation and string-order comparison pack|1|exponentiation|91|
|packed-decimal currency rounding and signed display-size pack|1|substring-predicate|72|
|financial exponentiation plus rounded currency overflow pack|1|string-collation|61|
|packed-decimal rounded currency and size-error pack|1|currency-rounding|19|
|decimal division with divide-by-zero and size-error pack|1|decimal-scale|14|
|rounded numeric target and size-error pack|1|numeric-conformance|9|
|numeric conformance predicate pack|1|screen-event-routing|7|
|substring/prefix predicate and multi-axis evaluate pack|1|date-arithmetic|5|
|invoice line aggregation with currency scale and numeric conformance pack|1|size-error-overflow|1|
|mortgage amortization formula pack with exponentiation and decimal precision|1|||
|numeric text parsing and decimal-point validation pack|1|||
|CICS screen-event routing pack|1|||
|CICS mortgage screen-flow and DB2 state pack|1|||

## Fidelity-event distribution

|Kind|Run 1|Run 2|
|---|---:|---:|
|boundary|22|0|
|none|5|241|
|precedence|5|91|
|rounding|11|33|
|sign|2|0|
|truncation|3|73|
|type-coercion|9|82|

## Verb frequency

|Verb|Run 1|Run 2|
|---|---:|---:|
|forbid|3|41|
|permit|10|132|
|remember|16|31|
|require|2|0|

## Hypothesis test

Run 2 **refutes** the Run 1 currency-pack hypothesis. In Run 2, `34` of `279` pack-needed rules (12.2%) fall into the `currency-rounding` + `decimal-scale` + `size-error-overflow` cluster; the remaining `245` pack-needed rules fall elsewhere.

## Larger-corpus signal

The larger corpus exposed many more screen/menu routing, substring, numeric-conformance, and intrinsic-function cases than Run 1 could show. It also made de-duplication a first-order concern: repeated GitHub learning examples and fork-like copies would inflate confidence if counted independently.

## Honesty boundary

This is corroboration, not replication. The corpora have different selection pressure, the Run 2 pass uses heuristic extraction and de-duplication, and no external COBOL auditor certified the generated classifications.

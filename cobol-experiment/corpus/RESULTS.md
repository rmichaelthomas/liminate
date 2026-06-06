# COBOL -> Liminate Expressibility & Fidelity Experiment - Run 1

## Run header

- Date: 2026-06-06
- Interpreter version: Liminate 0.14.1
- learn_cobol SHA: `2f9d6b3a747454a427489419d6cf1f5806861829`
- cobol-samples SHA: `11ad5f8c9fc80d0f3fd913ea30afc48bd506541d`
- mortgagesample SHA: `dd650c4d701bff7a12026e69530b87ca663c0037`
- Total programs scanned: 61
- Total with isolable rules: 32
- Total attempted: 32

## Expressibility table

|Outcome|Count|% of attempted|
|---|---:|---:|
|base vocabulary|18|56.2%|
|pack-needed|13|40.6%|
|untranslatable|1|3.1%|

## Pack-demand summary

|Pack needed|Count|
|---|---:|
|collation and string-order comparison pack|1|
|packed-decimal currency rounding and signed display-size pack|1|
|financial exponentiation plus rounded currency overflow pack|1|
|packed-decimal rounded currency and size-error pack|1|
|decimal division with divide-by-zero and size-error pack|1|
|rounded numeric target and size-error pack|1|
|numeric conformance predicate pack|1|
|substring/prefix predicate and multi-axis evaluate pack|1|
|invoice line aggregation with currency scale and numeric conformance pack|1|
|mortgage amortization formula pack with exponentiation and decimal precision|1|
|numeric text parsing and decimal-point validation pack|1|
|CICS screen-event routing pack|1|
|CICS mortgage screen-flow and DB2 state pack|1|

## Fidelity-risk summary

|Event kind|Count|
|---|---:|
|boundary|22|
|none|5|
|precedence|5|
|rounding|11|
|sign|2|
|truncation|3|
|type-coercion|9|

|Program|Kind|COBOL|Liminate|Risk|
|---|---|---|---|---|
|AGE-CHECK|boundary|`age <= 21`|`age is below 22`|else branch made explicit; faithful for integer PIC 999 ages|
|RETIREMENT-AGE|boundary|`age >= 60`|`age is above 59`|inclusive-vs-exclusive; faithful for integer ages only|
|RETIREMENT-AGE|boundary|`age >= 65`|`age is above 64`|inclusive-vs-exclusive; faithful for integer ages only|
|PAY-CALCULATION|rounding|`COMPUTE pay ROUNDED`|`remember total-pay with standard-pay plus overtime-pay`|base Liminate arithmetic does not declare COBOL rounding mode|
|PAY-MODULAR-VERSION|boundary|`hours-worked <= 37.5`|`hours-worked is below 37.51`|inclusive decimal boundary assumes PIC 99V99 centesimal precision|
|PAY-MODULAR-VERSION|rounding|`COMPUTE pay ROUNDED`|`remember regular-pay with hours-worked multiplied by rate-of-pay`|target-picture rounding not represented in base vocabulary|
|ELECTRICITY-BILL|sign|`IF units NEGATIVE`|`forbid units is below 0`|negative usage is treated as rejection|
|ELECTRICITY-BILL|rounding|`COMPUTE charge ROUNDED`|`remember charge with basic-charge plus extra-charge`|COBOL target rounding is not represented|
|PROCESS-MARKS|boundary|`40 THRU 49.9`|`average-mark is above 39.9 and average-mark is below 50`|inclusive range rewritten through strict operators|
|PROCESS-MARKS|boundary|`50 THRU 59.9`|`average-mark is above 49.9 and average-mark is below 60`|inclusive range rewritten through strict operators|
|PROCESS-MARKS|boundary|`60 THRU 69.9`|`average-mark is above 59.9 and average-mark is below 70`|inclusive range rewritten through strict operators|
|PROCESS-MARKS|boundary|`70 THRU 100`|`average-mark is above 69.9 and average-mark is below 100.1`|upper boundary assumes one decimal place for the average|
|TIME-AND-DATE|boundary|`date-in-yy < 96`|`date-year is below 96`|strict less-than is direct|
|TIME-AND-DATE|boundary|`date-in-yy >= 96`|`date-year is above 95`|else branch inclusive boundary made explicit for integer YY|
|DISCOUNT|rounding|`GIVING discounted-charge ROUNDED`|`discounted-charge with charge minus discount`|base Liminate does not declare COBOL rounded target-picture behavior|
|SHOPPING-BILL|rounding|`ADD item-cost TO total-bill ROUNDED`|`total-bill plus item-cost`|base Liminate does not model rounded accumulation into the target field|
|NET-PAY|rounding|`GIVING net-pay ROUNDED`|`not expressed`|rounded signed display target must be preserved|
|NET-PAY|sign|`PIC +999.99`|`not expressed`|display sign behavior is part of the financial result|
|COMPOUND-INTEREST|rounding|`COMPUTE amount-at-end ROUNDED`|`not expressed`|target rounding and overflow are material|
|INVESTIMENT|rounding|`GIVING temp ROUNDED / interest ROUNDED / amount-end-out ROUNDED`|`not expressed`|multiple rounded targets affect the final amount|
|ADD-WITH-SIZE-ERROR|rounding|`ADD in-1 TO in-2 GIVING result-1 ROUNDED`|`not expressed`|rounded target behavior must be explicit|
|COND88-AGE-RANGES|boundary|`0 THRU 12`|`person-age is above -1 and person-age is below 13`|inclusive integer range rewritten through strict operators|
|COND88-AGE-RANGES|boundary|`13 THRU 19`|`person-age is above 12 and person-age is below 20`|inclusive integer range rewritten through strict operators|
|COND88-AGE-RANGES|boundary|`20 THRU 35`|`person-age is above 19 and person-age is below 36`|inclusive integer range rewritten through strict operators|
|COND88-AGE-RANGES|boundary|`36 THRU 49`|`person-age is above 35 and person-age is below 50`|inclusive integer range rewritten through strict operators|
|COND88-AGE-RANGES|boundary|`50 THRU 59`|`person-age is above 49 and person-age is below 60`|inclusive integer range rewritten through strict operators|
|COND88-AGE-RANGES|boundary|`60 THRU 74`|`person-age is above 59 and person-age is below 75`|inclusive integer range rewritten through strict operators|
|COND88-AGE-RANGES|boundary|`75 THRU 200`|`person-age is above 74 and person-age is below 201`|inclusive integer range rewritten through strict operators|
|IFEVAL-DIVIDE-GUARD|boundary|`NUMERIC-1 IS GREATER THAN ZERO`|`divisor is above 0`|strict positive boundary is direct|
|INVCALC|rounding|`packed decimal line totals and tax fields`|`not expressed`|currency scale and tax precision affect totals|
|EPSMPMT-VALIDATION|boundary|`EPSPDATA-PRINCIPLE-DATA > 0`|`principal-amount is above 0`|strict positive boundary is direct|
|EPSMPMT-VALIDATION|boundary|`EPSPDATA-PRINCIPLE-DATA > STATIC-MAXIMUM-PRINCIPLE`|`forbid principal-amount is above maximum-principal`|strict maximum boundary is direct|
|EPSMPMT-VALIDATION|boundary|`EPSPDATA-QUOTED-INTEREST-RATE <= 0`|`require quoted-interest-rate is above 0`|negative/zero interest rejection restated as positive requirement|
|EPSMPMT-PAYMENT-FORMULA|rounding|`EPSPDATA-RETURN-MONTH-PAYMENT target`|`not expressed`|payment precision is financially material|
|EPSNBRVL-NUMBER-PARSER|boundary|`UNTIL WS-IDX > WS-END-SPACE / < WS-LEADING-SPACES`|`not expressed`|loop boundaries govern which characters are accepted|

## Verb-frequency table

|Verb|Count|
|---|---:|
|remember|16|
|permit|10|
|forbid|3|
|require|2|

## Three findings

- Base Liminate carried the small threshold, membership, guard, and arithmetic rules, but COBOL's financial target semantics pushed many realistic calculations into pack-needed territory.
- The strongest pack-demand signal is not COBOL syntax itself; it is domain fidelity around rounded packed decimals, size-error paths, numeric conformance, string slicing, and amortization.
- The fidelity surface is concentrated in boundaries and rounding: the translations that pass are readable precisely because every inclusive range, else-branch boundary, and rounded target is called out instead of hidden.

## Honesty boundary

This run uses a small learning/sample corpus, not production mainframe portfolios; it uses one interpreter version, Liminate 0.14.1; and no human COBOL auditor or bank compliance reviewer certified the translations.

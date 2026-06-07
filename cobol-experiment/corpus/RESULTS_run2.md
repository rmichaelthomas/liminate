# COBOL -> Liminate Expressibility & Fidelity Experiment - Run 2

## Run header

- Date: 2026-06-06
- Interpreter version: Liminate 0.14.1
- X-COBOL release: 2024-scale corpus inferred from 5,195 COBOL files; local `zenodo_record.json` reports record `7968845` / DOI `10.5281/zenodo.7968845`, so the metadata is recorded as stale or mixed.
- Total files in corpus: 5195
- Files triaged: 2282
- Files with isolable rules detected: 1850
- Rules attempted: 520
- Duplicates collapsed: 249

## Expressibility table

|Outcome|Count|% of attempted|
|---|---:|---:|
|base vocabulary|204|39.2%|
|pack-needed|279|53.7%|
|untranslatable|37|7.1%|

## Pack-demand summary

|Pack needed|Count|
|---|---:|
|exponentiation|91|
|substring-predicate|72|
|string-collation|61|
|currency-rounding|19|
|decimal-scale|14|
|numeric-conformance|9|
|screen-event-routing|7|
|date-arithmetic|5|
|size-error-overflow|1|

## Fidelity-risk summary

|Event kind|Count|
|---|---:|
|none|241|
|precedence|91|
|type-coercion|82|
|truncation|73|
|rounding|33|

|Program|Kind|COBOL|Liminate|Risk|
|---|---|---|---|---|
|ASREA748|rounding|`00207 COMPUTE FA-FROZ-EQLZD ROUNDED =`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|ASREA748|rounding|`00209 COMPUTE FA-FROZ-TXAMT ROUNDED =`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|ASREA748|rounding|`00211 COMPUTE FA-EXPINCEV ROUNDED =`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|ASREA748|rounding|`00213 COMPUTE FA-EXPINCTX ROUNDED =`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|MEDCLAIM|rounding|`COMPUTE CLAIMPAID-WS ROUNDED =`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|MEDCLAIM|rounding|`COMPUTE CLAIMPAID-WS ROUNDED = CLAIM-AMOUNT -`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|MEDCLAIM|rounding|`COMPUTE DEDUCTIBLE-WS ROUNDED =`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|PROG12-2|rounding|`WS-ANNUAL-EARN ROUNDED.`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|PROG12-2|rounding|`WS-TMP-TAXABLE-EARN ROUNDED.`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|PROG14-2|rounding|`COMPUTE PREV-SEM-GPA ROUNDED = GP-SM/CREDITS-SM`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|WS81C|rounding|`COMPUTE WS-RFP-P1 ROUNDED = WS-Price-Keyboards -`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|WS81C|rounding|`COMPUTE WS-RFP-P1 ROUNDED = WS-Price-Keyboards +`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|WS81C|rounding|`COMPUTE WS-RFP-P1 ROUNDED = WS-Price-Vocals -`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|WS81C|rounding|`COMPUTE WS-RFP-P1 ROUNDED = WS-Price-Vocals +`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|WS81C|rounding|`COMPUTE WS-RFP-P1 ROUNDED = WS-Price-Guitar -`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|WS81C|rounding|`COMPUTE WS-RFP-P1 ROUNDED = WS-Price-Guitar +`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|WS81C|rounding|`COMPUTE WS-RFP-P1 ROUNDED = WS-Price-Bass -`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|1brc|rounding|`COMPUTE WS-MEAS-MEAN(WS-IDX) ROUNDED =`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|PROGCOB11|rounding|`COMPUTE WRK-AREA = (WRK-LARGURA * WRK-COMPRIMENTO)`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|PROGCOB07|rounding|`COMPUTE WRK-MEDIA = (WRK-NOTA1 + WRK-NOTA2) / 2.`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|lgwebst5|rounding|`Compute NCountVal = (HHVal * 3600) +`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|lgwebst5|rounding|`Compute OCountVal = (HHVal * 3600) +`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|payroll|rounding|`COMPUTE FS-TOTAL-HE = ( (FS-SALBA / FS-CH) + (FS-SALBA / FS-C`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|payroll|rounding|`COMPUTE FS-DSR = (FS-TOTAL-HE / 26) * 4.`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|payroll|rounding|`COMPUTE FS-IRRF = (((FS-SALBR - FS-INSS) - FS-TOTAL-DEP)`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|payroll|rounding|`COMPUTE FS-TOTAL-FALTAS = (FS-SALBA / 30) * FS-FALTAS.`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|gol|rounding|`COMPUTE cell_random ROUNDED = random_seed`|`not expressed in base vocabulary`|currency-rounding semantics are material to the COBOL rule|
|swathi_cobolChallenge_22|rounding|`COMPUTE WS-TICKET = ( WS-PRICE * 50 ) / 100`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|swathi_cobolChallenge_22|rounding|`COMPUTE WS-TICKET = ( WS-PRICE * 40 ) / 100`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|swathi_cobolChallenge_22|rounding|`COMPUTE WS-TICKET = ( WS-PRICE * 20 ) / 100`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|employee-salary|rounding|`COMPUTE ALLW = LBS * ( 1 + LDA / 100 )`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|credit_card-sample-full|rounding|`COMPUTE WS-total-amount = (WS-total-amount + WS-C1-IMPORTE)`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|
|HELLO-WORLD|rounding|`COMPUTE Y = (((X + 1) - 1) * 6) / 3`|`not expressed in base vocabulary`|decimal-scale semantics are material to the COBOL rule|

## Verb-frequency table

|Verb|Count|
|---|---:|
|permit|132|
|forbid|41|
|remember|31|

## Three findings

- Base Liminate accepted 204 of 520 isolated rules (39.2%), mainly simple thresholds, equality checks, and arithmetic assignments.
- Pack demand remained substantial at 279 rules (53.7%); the leading label was `exponentiation`, showing that COBOL-specific runtime semantics still dominate the growth surface.
- Fidelity risk was concentrated in `none` events; every generated boundary conversion was surfaced through both `because` text and the notes schema.

## Honesty boundary

This is a large but still open-source GitHub COBOL corpus, not certified production bank mainframe code. The pass used one interpreter version, Liminate 0.14.1. No human COBOL auditor certified the translations. De-duplication is heuristic and the generator intentionally classifies uncertain COBOL semantics as pack-needed rather than forcing base vocabulary.

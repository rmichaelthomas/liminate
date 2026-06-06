      * Source excerpt from X-COBOL.
      * Attribution: tanto259/cobol-course; file tanto259@cobol-course/MEDCLAIM.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L183:        250-CALCULATE-DEDUCTIBLE.
      * L184:            MOVE 'N' TO DEDUCTIBLE-ST.
      * L185: 
      * L186:            COMPUTE DEDUCTIBLE-WS ROUNDED =
      * L187:                 POLICY-AMOUNT * DEDUC-PCTG.
      * L188: 
      * L189:            IF POLICY-DEDUCTIBLE-PAID >= DEDUCTIBLE-WS

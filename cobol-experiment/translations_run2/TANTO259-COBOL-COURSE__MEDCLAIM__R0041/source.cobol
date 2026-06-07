      * Source excerpt from X-COBOL.
      * Attribution: tanto259/cobol-course; file tanto259@cobol-course/MEDCLAIM.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L167:        250-CALCULATE-CLAIM.
      * L168:            PERFORM 250-CALCULATE-DEDUCTIBLE.
      * L169:            IF DEDUCTIBLE-MET
      * L170:                 COMPUTE CLAIMPAID-WS ROUNDED =
      * L171:                     CLAIM-AMOUNT - (POLICY-COINSURANCE * CLAIM-AMOUNT)
      * L172:            ELSE
      * L173:                 COMPUTE CLAIMPAID-WS ROUNDED = CLAIM-AMOUNT -

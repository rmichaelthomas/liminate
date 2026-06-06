      * Source excerpt from X-COBOL.
      * Attribution: tanto259/cobol-course; file tanto259@cobol-course/MEDCLAIM.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L170:                 COMPUTE CLAIMPAID-WS ROUNDED =
      * L171:                     CLAIM-AMOUNT - (POLICY-COINSURANCE * CLAIM-AMOUNT)
      * L172:            ELSE
      * L173:                 COMPUTE CLAIMPAID-WS ROUNDED = CLAIM-AMOUNT -
      * L174:                     DEDUCTIBLE-WS - (POLICY-COINSURANCE * CLAIM-AMOUNT)
      * L175:            END-IF.
      * L176: 

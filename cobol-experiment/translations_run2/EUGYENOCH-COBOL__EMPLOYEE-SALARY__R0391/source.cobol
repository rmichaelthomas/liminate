      * Source excerpt from X-COBOL.
      * Attribution: eugyenoch/cobol; file eugyenoch@cobol/employee-salary.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L191: MOVE ZERO TO RPAY
      * L192: COMPUTE ALLW = LBS * ( 1 + LDA / 100 )
      * L193: COMPUTE RPAY = ALLW + LOB
      * L194: COMPUTE LPFD = LPFD + LITAX
      * L195: COMPUTE RPAY = RPAY â LPFD
      * L196: IF MOD =âYâ OR MOD =âYâ THEN
      * L197: MOVE RPAY TO TT-SALARY

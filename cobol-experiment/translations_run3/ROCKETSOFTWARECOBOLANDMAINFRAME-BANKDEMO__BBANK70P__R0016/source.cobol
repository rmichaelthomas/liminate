      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: RocketSoftwareCOBOLandMainframe/BankDemo; file RocketSoftwareCOBOLandMainframe@BankDemo/BBANK70P.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L451:            IF WS-CALC-WORK-TERM IS EQUAL TO ZERO
      * L452:               MOVE 'Please enter a non-zero term'
      * L453:                 TO WS-ERROR-MSG
      * L454:               GO TO VALIDATE-TERM-ERROR
      * L455:            END-IF.
      * L456:            IF WS-CALC-WORK-TERM-N IS GREATER THAN 1200
      * L457:               MOVE 'Term exceeds 100 years!'
      * L458:                 TO WS-ERROR-MSG
      * L459:               GO TO VALIDATE-TERM-ERROR
      * L460:            END-IF.

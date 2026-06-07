      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: RocketSoftwareCOBOLandMainframe/BankDemo; file RocketSoftwareCOBOLandMainframe@BankDemo/BBANK70P.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L408:            MOVE WS-CALC-WORK-RATE-P2 (1:3) TO WS-CALC-WORK-PERC (4:3).
      * L409: 
      * L410:            IF WS-CALC-WORK-PERC-N IS NOT GREATER THAN ZERO
      * L411:               MOVE 'Nothing''s free. Rate must be greater than 0%'
      * L412:                 TO WS-ERROR-MSG
      * L413:               GO TO VALIDATE-RATE-ERROR
      * L414:            END-IF.

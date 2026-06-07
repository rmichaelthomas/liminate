      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: RocketSoftwareCOBOLandMainframe/BankDemo; file RocketSoftwareCOBOLandMainframe@BankDemo/BBANK30P.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L454:        CALC-SERVICE-CHARGE.
      * L455:            IF WS-SRV-BAL IS EQUAL TO SPACES
      * L456:               MOVE 0 TO WS-SRV-AMT
      * L457:               GO TO CALC-SERVICE-CHARGE-EDIT
      * L458:            END-IF.
      * L459:            IF WS-SRV-BAL-N IS GREATER THAN WS-SRV-BAL5
      * L460:               MOVE WS-SRV-CHG5 TO WS-SRV-AMT
      * L461:               GO TO CALC-SERVICE-CHARGE-EDIT
      * L462:            END-IF.
      * L463:            IF WS-SRV-BAL-N IS GREATER THAN WS-SRV-BAL4
      * L464:               MOVE WS-SRV-CHG4 TO WS-SRV-AMT
      * L465:               GO TO CALC-SERVICE-CHARGE-EDIT
      * L466:            END-IF.
      * L467:            IF WS-SRV-BAL-N IS GREATER THAN WS-SRV-BAL3
      * L468:               MOVE WS-SRV-CHG3 TO WS-SRV-AMT
      * L469:               GO TO CALC-SERVICE-CHARGE-EDIT
      * L470:            END-IF.
      * L471:            IF WS-SRV-BAL-N IS GREATER THAN WS-SRV-BAL2
      * L472:               MOVE WS-SRV-CHG2 TO WS-SRV-AMT
      * L473:               GO TO CALC-SERVICE-CHARGE-EDIT
      * L474:            END-IF.
      * L475:            IF WS-SRV-BAL-N IS GREATER THAN WS-SRV-BAL1
      * L476:               MOVE WS-SRV-CHG1 TO WS-SRV-AMT
      * L477:               GO TO CALC-SERVICE-CHARGE-EDIT
      * L478:            ELSE
      * L479:               MOVE WS-SRV-CHG0 TO WS-SRV-AMT
      * L480:               GO TO CALC-SERVICE-CHARGE-EDIT
      * L481:            END-IF.

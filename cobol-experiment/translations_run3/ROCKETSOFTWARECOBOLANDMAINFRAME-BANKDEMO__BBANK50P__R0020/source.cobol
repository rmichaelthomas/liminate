      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: RocketSoftwareCOBOLandMainframe/BankDemo; file RocketSoftwareCOBOLandMainframe@BankDemo/BBANK50P.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L454:            END-IF.
      * L455:            IF WS-XFER-AMT-NUM-N IS GREATER THAN WS-XFER-ACCT-FROM-BAL-N
      * L456:               MOVE 'Insufficient funds in from account'
      * L457:                 TO WS-ERROR-MSG
      * L458:               GO TO VALIDATE-DATA-ERROR

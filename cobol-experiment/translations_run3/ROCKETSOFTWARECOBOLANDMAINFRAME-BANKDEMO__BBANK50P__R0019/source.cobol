      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: RocketSoftwareCOBOLandMainframe/BankDemo; file RocketSoftwareCOBOLandMainframe@BankDemo/BBANK50P.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L448:                 GIVING WS-XFER-ACCT-TO-BAL-N
      * L449:            END-IF.
      * L450:            IF WS-XFER-ACCT-FROM-BAL-N IS LESS THAN ZERO
      * L451:               MOVE 'Cannot transfer from a negative balance'
      * L452:                 TO WS-ERROR-MSG
      * L453:               GO TO VALIDATE-DATA-ERROR

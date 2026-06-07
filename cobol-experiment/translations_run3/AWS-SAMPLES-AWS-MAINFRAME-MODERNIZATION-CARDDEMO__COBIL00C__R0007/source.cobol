      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: aws-samples/aws-mainframe-modernization-carddemo; file aws-samples@aws-mainframe-modernization-carddemo/COBIL00C.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L197:            IF NOT ERR-FLG-ON
      * L198:                IF ACCT-CURR-BAL <= ZEROS AND
      * L199:                   ACTIDINI OF COBIL0AI NOT = SPACES AND LOW-VALUES
      * L200:                    MOVE 'Y'     TO WS-ERR-FLG
      * L201:                    MOVE 'You have nothing to pay...' TO
      * L202:                                    WS-MESSAGE
      * L203:                    MOVE -1       TO ACTIDINL OF COBIL0AI
      * L204:                    PERFORM SEND-BILLPAY-SCREEN
      * L205:                END-IF

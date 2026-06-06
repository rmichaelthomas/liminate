      * Source excerpt from X-COBOL.
      * Attribution: derekjj/Mainframe-Dev; file derekjj@Mainframe-Dev/DCIA2PGC.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L73:            IF ACCTNOI = "XXXXX" THEN
      * L74:                 GO TO 999-EXIT
      * L75:            ELSE
      * L76:            IF ACCTNOL < 5 THEN
      * L77:                 MOVE "ACCOUNT NUMBERS MUST BE 5 NUMBERS LONG"
      * L78:                     TO WS-MESSAGE
      * L79:                 GO TO 500-REPORT-ERROR

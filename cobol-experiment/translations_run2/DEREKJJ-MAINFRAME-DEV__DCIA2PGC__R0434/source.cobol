      * Source excerpt from X-COBOL.
      * Attribution: derekjj/Mainframe-Dev; file derekjj@Mainframe-Dev/DCIA2PGC.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L107:                     TO WS-MESSAGE
      * L108:                 GO TO 500-REPORT-ERROR
      * L109:            ELSE
      * L110:            IF CRLIMITL < 3 THEN
      * L111:                 MOVE "LIMIT MUST BE 100 TO 99999999 INCLUSIVE"
      * L112:                     TO WS-MESSAGE
      * L113:                 GO TO 500-REPORT-ERROR

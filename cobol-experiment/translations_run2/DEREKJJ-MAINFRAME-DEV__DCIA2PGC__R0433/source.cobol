      * Source excerpt from X-COBOL.
      * Attribution: derekjj/Mainframe-Dev; file derekjj@Mainframe-Dev/DCIA2PGC.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L102:                     TO WS-MESSAGE
      * L103:                 GO TO 500-REPORT-ERROR
      * L104:            ELSE
      * L105:            IF CRLIMITI(1:CRLIMITL) IS NOT NUMERIC THEN
      * L106:                 MOVE "LIMIT MUST BE NUMERIC"
      * L107:                     TO WS-MESSAGE
      * L108:                 GO TO 500-REPORT-ERROR

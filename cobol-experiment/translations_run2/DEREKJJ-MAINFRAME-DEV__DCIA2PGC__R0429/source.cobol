      * Source excerpt from X-COBOL.
      * Attribution: derekjj/Mainframe-Dev; file derekjj@Mainframe-Dev/DCIA2PGC.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L85:                 MOVE "FIRST NAME REQUIRED" TO WS-MESSAGE
      * L86:                 GO TO 500-REPORT-ERROR
      * L87:            ELSE
      * L88:            IF SNAMEL = 0 THEN
      * L89:                 MOVE "SIR NAME REQUIRED" TO WS-MESSAGE
      * L90:                 GO TO 500-REPORT-ERROR
      * L91:            ELSE

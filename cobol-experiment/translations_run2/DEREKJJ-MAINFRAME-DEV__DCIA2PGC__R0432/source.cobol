      * Source excerpt from X-COBOL.
      * Attribution: derekjj/Mainframe-Dev; file derekjj@Mainframe-Dev/DCIA2PGC.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L97:                 MOVE "ADDRESS REQUIRED" TO WS-MESSAGE
      * L98:                 GO TO 500-REPORT-ERROR
      * L99:            ELSE
      * L100:            IF STATI NOT EQUAL "A" AND "B" AND "X" AND "Z" THEN
      * L101:                 MOVE "ERROR. STATUS OPTIONS ARE A, B, X, OR Z."
      * L102:                     TO WS-MESSAGE
      * L103:                 GO TO 500-REPORT-ERROR

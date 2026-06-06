      * Source excerpt from X-COBOL.
      * Attribution: lauryndbrown/Cisp; file lauryndbrown@Cisp/recursion.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L212:            MOVE COMMAND-RESULT TO LS-COMMAND-RESULT.
      * L213:            MOVE COMMAND-RETURN-ID TO WS-LAST-ID.
      * L214:            DELETE CALL-STACK RECORD.
      * L215:            IF COMMAND-ID = WS-OLDEST-ID THEN
      * L216:                SET WS-STACK-IS-EMPTY-YES TO TRUE
      * L217:            END-IF.
      * L218:       D     DISPLAY "DELETED:" COMMAND-ID " GOTO:" WS-LAST-ID.

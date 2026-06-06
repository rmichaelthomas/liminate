      * Source excerpt from X-COBOL.
      * Attribution: lauryndbrown/Cisp; file lauryndbrown@Cisp/cisp.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L65:        EVALUTE-LISP-PROCEDURE.
      * L66:       ********* Evalute lisp
      * L67:             MOVE "ADD" TO WS-LOG-OPERATION-FLAG.
      * L68:             MOVE "LISP" TO WS-LOG-RECORD-FUNCTION-NAME.
      * L69:             MOVE "Starting Lisp Evalutation" TO WS-LOG-RECORD-MESSAGE.
      * L70:             CALL 'LOGGER' USING WS-LOG-OPERATION-FLAG, WS-LOG-RECORD.
      * L71:             CALL "LISP" USING WS-LISP-SYMBOLS.

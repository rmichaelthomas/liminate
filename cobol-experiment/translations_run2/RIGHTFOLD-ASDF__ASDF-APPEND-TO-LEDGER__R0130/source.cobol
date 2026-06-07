      * Source excerpt from X-COBOL.
      * Attribution: rightfold/asdf; file rightfold@asdf/asdf-append-to-ledger.cob.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L56:            CALL 'asdf-parse-uuid' USING ws-uuid-text fs-creditor
      * L57: 
      * L58:            ACCEPT ws-amount FROM ARGUMENT-VALUE
      * L59:            IF FUNCTION TRIM(ws-amount) IS NUMERIC THEN
      * L60:                MOVE FUNCTION TRIM(ws-amount) TO fs-amount
      * L61:            ELSE
      * L62:                DISPLAY 'Non-numeric amount' WITH NO ADVANCING

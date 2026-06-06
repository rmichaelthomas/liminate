      * Source excerpt from X-COBOL.
      * Attribution: rightfold/asdf; file rightfold@asdf/asdf-append-to-ledger.cob.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L38:            CALL 'asdf-parse-uuid' USING ws-uuid-text ws-group
      * L39: 
      * L40:            ACCEPT fs-type FROM ARGUMENT-VALUE
      * L41:            IF fs-type IS NOT EQUAL TO 'D' AND 'P' THEN
      * L42:                DISPLAY 'Invalid type' WITH NO ADVANCING
      * L43:                GO TO para-invalid-parse
      * L44:            END-IF

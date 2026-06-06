      * Source excerpt from X-COBOL.
      * Attribution: rightfold/asdf; file rightfold@asdf/asdf-append-to-ledger.cob.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L44:            END-IF
      * L45: 
      * L46:            ACCEPT fs-comment FROM ARGUMENT-VALUE
      * L47:            IF fs-comment IS EQUAL TO ALL SPACES THEN
      * L48:                DISPLAY 'Empty comment' WITH NO ADVANCING
      * L49:                GO TO para-invalid-parse
      * L50:            END-IF

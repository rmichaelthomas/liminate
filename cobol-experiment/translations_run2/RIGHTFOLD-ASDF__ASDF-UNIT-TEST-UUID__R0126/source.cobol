      * Source excerpt from X-COBOL.
      * Attribution: rightfold/asdf; file rightfold@asdf/asdf-unit-test-uuid.cob.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L18:            CALL 'asdf-generate-uuid' USING ws-uuid
      * L19:            CALL 'asdf-format-uuid' USING ws-uuid ws-formatted
      * L20:            CALL 'asdf-parse-uuid' USING ws-formatted ws-parsed
      * L21:            IF ws-parsed IS NOT EQUAL TO ws-uuid THEN
      * L22:                DISPLAY 'UUID roundtrip not successful'
      * L23:                MOVE 1 TO RETURN-CODE
      * L24:                STOP RUN

      * Source excerpt from X-COBOL.
      * Attribution: lauryndbrown/Cisp; file lauryndbrown@Cisp/tokenizer.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L152:              WS-COUNT = 100 OR WS-FLAG
      * L153:                UNSTRING WS-IN-LISP-RECORD DELIMITED BY ALL ' ' INTO
      * L154:                LS-SYMBOL(WS-COUNT) WITH POINTER STRING-PTR
      * L155:                IF LS-SYMBOL(WS-COUNT) = SPACES THEN
      * L156:                    SET WS-FLAG-YES TO TRUE
      * L157:                ELSE
      * L158:                    ADD 1 TO LS-SYMBOL-TABLE-SIZE

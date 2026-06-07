      * Source excerpt from X-COBOL.
      * Attribution: lauryndbrown/Cisp; file lauryndbrown@Cisp/tokenizer.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L89:            MOVE 0 TO WS-PARSE-EXPRESSION-LEN.
      * L90:            PERFORM VARYING WS-PARSE-STR-INDEX FROM 1 BY 1 UNTIL
      * L91:            WS-PARSE-HAS-ENDED OR WS-PARSE-STR-INDEX > 100
      * L92:                IF LS-SYMBOL(WS-COUNT)(WS-PARSE-STR-INDEX:1) = " " THEN
      * L93:                    SET WS-PARSE-HAS-ENDED TO TRUE
      * L94:                ELSE
      * L95:                    ADD 1 TO WS-PARSE-EXPRESSION-LEN

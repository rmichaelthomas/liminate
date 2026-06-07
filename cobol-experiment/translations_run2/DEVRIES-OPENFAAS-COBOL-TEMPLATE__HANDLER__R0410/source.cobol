      * Source excerpt from X-COBOL.
      * Attribution: devries/openfaas-cobol-template; file devries@openfaas-cobol-template/handler.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L24:             AT END SET end-of-file TO TRUE
      * L25:        END-READ.
      * L26: 
      * L27:        IF stdin-record = SPACE or stdin-record = LOW-VALUE THEN
      * L28:           DISPLAY "HELLO WORLD"
      * L29:        ELSE
      * L30:           DISPLAY "HELLO " stdin-record

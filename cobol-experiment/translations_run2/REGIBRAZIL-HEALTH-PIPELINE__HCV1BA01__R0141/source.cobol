      * Source excerpt from X-COBOL.
      * Attribution: RegiBrazil/health-pipeline; file RegiBrazil@health-pipeline/HCV1BA01.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L98:       *    ADD WS-CUSTOMER-LEN  TO WS-REQUIRED-CA-LEN
      * L99: 
      * L100:       * if less set error return code and return to caller
      * L101:            IF EIBCALEN IS LESS THAN WS-REQUIRED-CA-LEN
      * L102:              MOVE '98' TO CA-RETURN-CODE
      * L103:              EXEC CICS RETURN END-EXEC
      * L104:            END-IF

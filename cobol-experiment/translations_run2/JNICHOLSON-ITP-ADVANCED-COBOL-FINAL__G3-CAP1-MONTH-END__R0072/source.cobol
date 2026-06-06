      * Source excerpt from X-COBOL.
      * Attribution: jnicholson/ITP-Advanced-COBOL-FINAL; file jnicholson@ITP-Advanced-COBOL-FINAL/G3-CAP1-MONTH-END.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L63:                    MOVE 'Y' TO WS-CC-EOF
      * L64:                NOT AT END
      * L65:                    IF CC-ID EQUAL TO CH-ID THEN
      * L66:                        IF TRAN-TYPE = 'W' THEN
      * L67:                            COMPUTE WS-TOTAL = WS-TOTAL + CC-TRAN-PRICE
      * L68:                        END-IF
      * L69:                        IF TRAN-TYPE = 'D' THEN

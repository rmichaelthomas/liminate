      * Source excerpt from X-COBOL.
      * Attribution: RegiBrazil/DemoHealthCare; file RegiBrazil@DemoHealthCare/HCTRESTW.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L304:                          RESP(RESP)
      * L305:                          RESP2(RESP2)
      * L306:            END-EXEC
      * L307:            IF RESP NOT = DFHRESP(NORMAL) THEN
      * L308:               DISPLAY 'Cannot get URIMAP container.'
      * L309:            ELSE
      * L310:               UNSTRING WS-RESID DELIMITED BY '/'

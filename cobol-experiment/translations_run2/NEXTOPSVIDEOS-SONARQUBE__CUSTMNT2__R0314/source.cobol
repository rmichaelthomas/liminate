      * Source excerpt from X-COBOL.
      * Attribution: nextopsvideos/sonarqube; file nextopsvideos@sonarqube/Custmnt2.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L272:                     RESP(RESPONSE-CODE)
      * L273:            END-EXEC.
      * L274:       *
      * L275:            IF      RESPONSE-CODE NOT = DFHRESP(NORMAL)
      * L276:                AND RESPONSE-CODE NOT = DFHRESP(NOTFND)
      * L277:                PERFORM 9999-TERMINATE-PROGRAM
      * L278:            END-IF.

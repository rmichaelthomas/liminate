      * Source excerpt from X-COBOL.
      * Attribution: nextopsvideos/sonarqube; file nextopsvideos@sonarqube/Custmnt2.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L221:                            SET PROCESS-ADD-CUSTOMER TO TRUE
      * L222:                            MOVE SPACE TO CUSTOMER-MASTER-RECORD
      * L223:                        ELSE
      * L224:                            IF RESPONSE-CODE = DFHRESP(NORMAL)
      * L225:                                MOVE 'That customer already exists.'
      * L226:                                     TO MSG1O
      * L227:                                MOVE 'N' TO VALID-DATA-SW

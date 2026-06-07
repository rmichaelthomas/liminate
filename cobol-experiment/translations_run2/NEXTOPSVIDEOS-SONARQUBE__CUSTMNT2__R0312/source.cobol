      * Source excerpt from X-COBOL.
      * Attribution: nextopsvideos/sonarqube; file nextopsvideos@sonarqube/Custmnt2.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L216:                EVALUATE ACTIONI
      * L217:                    WHEN '1'
      * L218:                        PERFORM 1300-READ-CUSTOMER-RECORD
      * L219:                        IF RESPONSE-CODE = DFHRESP(NOTFND)
      * L220:                            MOVE ADD-INSTRUCTION TO INSTR2O
      * L221:                            SET PROCESS-ADD-CUSTOMER TO TRUE
      * L222:                            MOVE SPACE TO CUSTOMER-MASTER-RECORD

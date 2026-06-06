      * Source excerpt from X-COBOL.
      * Attribution: nextopsvideos/sonarqube; file nextopsvideos@sonarqube/Custmnt2.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L344:                    MOVE 'Customer record added.' TO MSG1O
      * L345:                    SET SEND-ERASE TO TRUE
      * L346:                ELSE
      * L347:                    IF RESPONSE-CODE = DFHRESP(DUPREC)
      * L348:                        MOVE 'Another user has added a record with that c
      * L349:       -                    'ustomer number.' TO MSG1O
      * L350:                        SET SEND-ERASE-ALARM TO TRUE

      * Source excerpt from X-COBOL.
      * Attribution: EstesE/COBOL; file EstesE@COBOL/PROG12-2.COB.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L341:                PERFORM VARYING IT-RATE-INDEX FROM 1 BY 1
      * L342:                    UNTIL IT-RATE-INDEX = 8 OR WS-EOT-SW = "Y"
      * L343: 
      * L344:                    IF WS-TAXABLE-EARN >=
      * L345:                        IT-LL-IN(IT-STATUS-INDEX,IT-RATE-INDEX) AND
      * L346:                       WS-TAXABLE-EARN <
      * L347:                        IT-UL-IN(IT-STATUS-INDEX,IT-RATE-INDEX) THEN

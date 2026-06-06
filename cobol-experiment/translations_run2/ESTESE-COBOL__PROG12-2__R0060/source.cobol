      * Source excerpt from X-COBOL.
      * Attribution: EstesE/COBOL; file EstesE@COBOL/PROG12-2.COB.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L336:                IT-STATUS-INDEX = 4 OR WS-EOT-SW = "Y"
      * L337: 
      * L338: 
      * L339:                IF WS-ER-MAR-STAT-IN = IT-STATUS-CODE-IN(IT-STATUS-INDEX)
      * L340:                    THEN
      * L341:                PERFORM VARYING IT-RATE-INDEX FROM 1 BY 1
      * L342:                    UNTIL IT-RATE-INDEX = 8 OR WS-EOT-SW = "Y"

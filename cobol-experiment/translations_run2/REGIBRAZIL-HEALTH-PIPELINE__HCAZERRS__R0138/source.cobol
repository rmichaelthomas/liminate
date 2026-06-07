      * Source excerpt from X-COBOL.
      * Attribution: RegiBrazil/health-pipeline; file RegiBrazil@health-pipeline/HCAZERRS.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L72:            EXEC CICS ASSIGN INVOKINGPROG(WS-INVOKEPROG)
      * L73:                 RESP(WS-RESP)
      * L74:            END-EXEC.
      * L75:            IF WS-INVOKEPROG NOT = SPACES
      * L76:               MOVE 'C' To WS-FLAG
      * L77:               MOVE COMMA-DATA  TO WRITE-MSG-MSG
      * L78:               MOVE EIBCALEN    TO WS-RECV-LEN

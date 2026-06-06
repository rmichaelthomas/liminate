      * Source excerpt from X-COBOL.
      * Attribution: RegiBrazil/health-pipeline; file RegiBrazil@health-pipeline/HCV1BA01.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L82:       * Process incoming commarea                                      *
      * L83:       *----------------------------------------------------------------*
      * L84:       * If NO commarea received issue an ABEND
      * L85:            IF EIBCALEN IS EQUAL TO ZERO
      * L86:                MOVE ' NO COMMAREA RECEIVED' TO EM-VARIABLE
      * L87:                PERFORM WRITE-ERROR-MESSAGE
      * L88:                EXEC CICS ABEND ABCODE('HCCA') NODUMP END-EXEC

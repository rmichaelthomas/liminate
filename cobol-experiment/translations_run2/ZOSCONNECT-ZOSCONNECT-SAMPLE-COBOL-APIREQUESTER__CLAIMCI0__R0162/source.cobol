      * Source excerpt from X-COBOL.
      * Attribution: zosconnect/zosconnect-sample-cobol-apirequester; file zosconnect@zosconnect-sample-cobol-apirequester/claimci0.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L110:                 RESP2(RSP-CLAIM-CICS-RESP2)
      * L111:            END-EXEC.
      * L112: 
      * L113:            IF RSP-CLAIM-CICS-RESP NOT = DFHRESP(NORMAL)
      * L114:                 MOVE 'EXEC CICS STARTBROWSE ERROR'
      * L115:                   TO WS-MSG-TO-WRITE
      * L116:                 PERFORM DO-WRITE-TO-CSMT

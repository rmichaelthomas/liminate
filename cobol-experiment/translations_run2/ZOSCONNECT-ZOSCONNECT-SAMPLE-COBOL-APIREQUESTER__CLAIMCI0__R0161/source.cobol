      * Source excerpt from X-COBOL.
      * Attribution: zosconnect/zosconnect-sample-cobol-apirequester; file zosconnect@zosconnect-sample-cobol-apirequester/claimci0.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L94:       * IF NO CHANNEL NAME WAS PASSED, THEN ASSIGN RETURNS SPACES.
      * L95:       * IF SPACES WERE RETURNED THEN TERMINATE WITH ABEND CODE NOCN
      * L96:       ******************************************************************
      * L97:            IF WS-CHANNEL-NAME = SPACES THEN
      * L98:                 EXEC CICS
      * L99:                      ABEND ABCODE('NOCN') NODUMP
      * L100:                 END-EXEC

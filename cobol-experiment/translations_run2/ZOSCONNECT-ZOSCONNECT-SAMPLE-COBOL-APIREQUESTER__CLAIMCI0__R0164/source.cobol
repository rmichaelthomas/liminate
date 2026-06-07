      * Source excerpt from X-COBOL.
      * Attribution: zosconnect/zosconnect-sample-cobol-apirequester; file zosconnect@zosconnect-sample-cobol-apirequester/claimci0.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L331:       * THE STATUS TO 'OKAY' OR 'PEND'.
      * L332:       ******************************************************************
      * L333:            IF BAQ-SUCCESS THEN
      * L334:               IF Xstatus2(1:Xstatus2-length) = 'Accepted'
      * L335:                  MOVE 'OKAY' TO RSP-CLAIM-STATUS
      * L336:               ELSE
      * L337:                  MOVE 'PEND' TO RSP-CLAIM-STATUS

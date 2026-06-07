      * Source excerpt from X-COBOL.
      * Attribution: bhbandam/AZ-Legacy-Engineering; file bhbandam@AZ-Legacy-Engineering/wtigbal.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L115:            MOVE 0 TO ACCT-BAL OF USER-DATA.
      * L116:            PERFORM GET-CUST-SSN THRU GET-CUST-SSN-EXIT.
      * L117: 
      * L118:            IF RET-CODE = 0 THEN
      * L119:               PERFORM GET-ACCT THRU GET-ACCT-EXIT
      * L120:            END-IF.
      * L121: 

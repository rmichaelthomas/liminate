      * Source excerpt from X-COBOL.
      * Attribution: bhbandam/AZ-Legacy-Engineering; file bhbandam@AZ-Legacy-Engineering/wtigbal.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L119:               PERFORM GET-ACCT THRU GET-ACCT-EXIT
      * L120:            END-IF.
      * L121: 
      * L122:            IF SERRORCODE NOT = 0 THEN
      * L123:               MOVE 1 TO SRETURNERRORTOCLIENT
      * L124:            END-IF.
      * L125:            EXEC CICS RETURN END-EXEC.

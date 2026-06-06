      * Source excerpt from X-COBOL.
      * Attribution: bhbandam/AZ-Legacy-Engineering; file bhbandam@AZ-Legacy-Engineering/BATCHVSAM.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L310: 026700           END-STRING                                             02670000
      * L311: 026800           PERFORM 2100-WRITE-RECORD THRU 2100-EXIT               02680000
      * L312: 026900                                                                  02690000
      * L313: 027000           MOVE    BOOKS-TITLE-TEXT(229:27) TO OP-TITLE           02700000
      * L314: 027100           PERFORM 2100-WRITE-RECORD THRU 2100-EXIT               02710000
      * L315: 027200                                                                  02720000
      * L316: 027300      WHEN BOOKS-TITLE-LEN > 152                                  02730000

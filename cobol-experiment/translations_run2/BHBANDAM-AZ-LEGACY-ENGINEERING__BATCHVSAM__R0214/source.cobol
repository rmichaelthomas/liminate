      * Source excerpt from X-COBOL.
      * Attribution: bhbandam/AZ-Legacy-Engineering; file bhbandam@AZ-Legacy-Engineering/BATCHVSAM.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L340: 029700           PERFORM 2100-WRITE-RECORD THRU 2100-EXIT               02970000
      * L341: 029800                                                                  02980000
      * L342: 029900      WHEN OTHER                                                  02990000
      * L343: 030000           MOVE    BOOKS-TITLE-TEXT(1:77) TO OP-TITLE             03000000
      * L344: 030100           PERFORM 2100-WRITE-RECORD THRU 2100-EXIT               03010000
      * L345: 030200      END-EVALUATE                                                03020000
      * L346: 030300                                                                  03030000

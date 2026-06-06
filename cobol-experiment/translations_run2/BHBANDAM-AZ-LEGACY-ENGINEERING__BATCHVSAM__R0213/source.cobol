      * Source excerpt from X-COBOL.
      * Attribution: bhbandam/AZ-Legacy-Engineering; file bhbandam@AZ-Legacy-Engineering/BATCHVSAM.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L336: 029300           END-STRING                                             02930000
      * L337: 029400           PERFORM 2100-WRITE-RECORD THRU 2100-EXIT               02940000
      * L338: 029500                                                                  02950000
      * L339: 029600           MOVE    BOOKS-TITLE-TEXT(77:77) TO OP-TITLE            02960000
      * L340: 029700           PERFORM 2100-WRITE-RECORD THRU 2100-EXIT               02970000
      * L341: 029800                                                                  02980000
      * L342: 029900      WHEN OTHER                                                  02990000

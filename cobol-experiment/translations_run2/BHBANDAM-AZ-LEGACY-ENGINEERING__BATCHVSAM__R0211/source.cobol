      * Source excerpt from X-COBOL.
      * Attribution: bhbandam/AZ-Legacy-Engineering; file bhbandam@AZ-Legacy-Engineering/BATCHVSAM.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L326: 028300           END-STRING                                             02830000
      * L327: 028400           PERFORM 2100-WRITE-RECORD THRU 2100-EXIT               02840000
      * L328: 028500                                                                  02850000
      * L329: 028600           MOVE    BOOKS-TITLE-TEXT(153:77) TO OP-TITLE           02860000
      * L330: 028700           PERFORM 2100-WRITE-RECORD THRU 2100-EXIT               02870000
      * L331: 028800                                                                  02880000
      * L332: 028900      WHEN BOOKS-TITLE-LEN > 77                                   02890000

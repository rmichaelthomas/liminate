      * Source excerpt from X-COBOL.
      * Attribution: bhbandam/AZ-Legacy-Engineering; file bhbandam@AZ-Legacy-Engineering/BATCHVSAM.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L330: 028700           PERFORM 2100-WRITE-RECORD THRU 2100-EXIT               02870000
      * L331: 028800                                                                  02880000
      * L332: 028900      WHEN BOOKS-TITLE-LEN > 77                                   02890000
      * L333: 029000           STRING BOOKS-TITLE-TEXT(1:76) DELIMITED BY SIZE        02900000
      * L334: 029100                  '-' DELIMITED BY SIZE                           02910000
      * L335: 029200                  INTO OP-TITLE                                   02920000
      * L336: 029300           END-STRING                                             02930000

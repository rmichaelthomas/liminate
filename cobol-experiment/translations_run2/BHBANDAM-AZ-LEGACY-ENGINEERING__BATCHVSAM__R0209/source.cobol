      * Source excerpt from X-COBOL.
      * Attribution: bhbandam/AZ-Legacy-Engineering; file bhbandam@AZ-Legacy-Engineering/BATCHVSAM.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L314: 027100           PERFORM 2100-WRITE-RECORD THRU 2100-EXIT               02710000
      * L315: 027200                                                                  02720000
      * L316: 027300      WHEN BOOKS-TITLE-LEN > 152                                  02730000
      * L317: 027400           STRING BOOKS-TITLE-TEXT(1:76) DELIMITED BY SIZE        02740000
      * L318: 027500                  '-' DELIMITED BY SIZE                           02750000
      * L319: 027600                  INTO OP-TITLE                                   02760000
      * L320: 027700           END-STRING                                             02770000

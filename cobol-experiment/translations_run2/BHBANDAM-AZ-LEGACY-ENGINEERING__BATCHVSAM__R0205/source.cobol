      * Source excerpt from X-COBOL.
      * Attribution: bhbandam/AZ-Legacy-Engineering; file bhbandam@AZ-Legacy-Engineering/BATCHVSAM.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L292: 024900                                                                  02490000
      * L293: 025000      EVALUATE TRUE                                               02500000
      * L294: 025100      WHEN BOOKS-TITLE-LEN > 228                                  02510000
      * L295: 025200           STRING BOOKS-TITLE-TEXT(1:76) DELIMITED BY SIZE        02520000
      * L296: 025300                  '-' DELIMITED BY SIZE                           02530000
      * L297: 025400                  INTO OP-TITLE                                   02540000
      * L298: 025500           END-STRING                                             02550000

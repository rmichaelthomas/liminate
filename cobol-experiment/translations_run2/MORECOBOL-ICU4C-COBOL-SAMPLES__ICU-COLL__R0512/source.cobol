      * Source excerpt from X-COBOL.
      * Attribution: morecobol/icu4c-cobol-samples; file morecobol@icu4c-cobol-samples/icu-Coll.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L321:        Collation-Main-Sort-sec  section.
      * L322:        Collation-Main-Sort.
      * L323:            Move      ZERO    to      Sort-Do-sw.
      * L324:            Compute   Sort-Count = Input-Record-Number - Main-Index.
      * L325:            Perform   Collation-Sort-sec
      * L326:                      Varying Sort-index  FROM 1 by 1
      * L327:                      until   Sort-index  > Sort-Count.

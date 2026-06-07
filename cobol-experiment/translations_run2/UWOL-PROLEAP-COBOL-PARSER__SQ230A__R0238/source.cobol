      * Source excerpt from X-COBOL.
      * Attribution: uwol/proleap-cobol-parser; file uwol@proleap-cobol-parser/SQ230A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L375: 037400     MOVE   "TEST(S) DELETED     " TO ENDER-DESC.                 SQ2304.2
      * L376: 037500     MOVE    CCVS-E-2 TO DUMMY-RECORD.                            SQ2304.2
      * L377: 037600     PERFORM WRITE-LINE.                                          SQ2304.2
      * L378: 037700     IF INSPECT-COUNTER EQUAL TO ZERO                             SQ2304.2
      * L379: 037800         MOVE   "NO " TO ERROR-TOTAL                              SQ2304.2
      * L380: 037900     ELSE                                                         SQ2304.2
      * L381: 038000         MOVE    INSPECT-COUNTER TO ERROR-TOTAL.                  SQ2304.2

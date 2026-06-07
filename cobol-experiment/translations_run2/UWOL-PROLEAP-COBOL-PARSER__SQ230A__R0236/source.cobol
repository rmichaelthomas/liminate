      * Source excerpt from X-COBOL.
      * Attribution: uwol/proleap-cobol-parser; file uwol@proleap-cobol-parser/SQ230A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L361: 036000     MOVE    CCVS-E-2        TO DUMMY-RECORD                      SQ2304.2
      * L362: 036100     PERFORM WRITE-LINE.                                          SQ2304.2
      * L363: 036200     MOVE   "TEST(S) FAILED" TO ENDER-DESC.                       SQ2304.2
      * L364: 036300     IF ERROR-COUNTER IS EQUAL TO ZERO                            SQ2304.2
      * L365: 036400         MOVE   "NO " TO ERROR-TOTAL                              SQ2304.2
      * L366: 036500     ELSE                                                         SQ2304.2
      * L367: 036600         MOVE    ERROR-COUNTER TO ERROR-TOTAL.                    SQ2304.2

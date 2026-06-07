      * Source excerpt from X-COBOL.
      * Attribution: INFINITE-TECHNOLOGY/COBOL; file INFINITE-TECHNOLOGY@COBOL/NC115A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L291: 029000      MOVE CCVS-E-2 TO DUMMY-RECORD PERFORM WRITE-LINE.           NC1154.2
      * L292: 029100  END-ROUTINE-12.                                                 NC1154.2
      * L293: 029200      MOVE "TEST(S) FAILED" TO ENDER-DESC.                        NC1154.2
      * L294: 029300     IF       ERROR-COUNTER IS EQUAL TO ZERO                      NC1154.2
      * L295: 029400         MOVE "NO " TO ERROR-TOTAL                                NC1154.2
      * L296: 029500         ELSE                                                     NC1154.2
      * L297: 029600         MOVE ERROR-COUNTER TO ERROR-TOTAL.                       NC1154.2

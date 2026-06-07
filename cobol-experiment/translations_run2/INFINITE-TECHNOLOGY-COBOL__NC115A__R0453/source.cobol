      * Source excerpt from X-COBOL.
      * Attribution: INFINITE-TECHNOLOGY/COBOL; file INFINITE-TECHNOLOGY@COBOL/NC115A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L303: 030200         MOVE DELETE-COUNTER TO ERROR-TOTAL.                      NC1154.2
      * L304: 030300     MOVE "TEST(S) DELETED     " TO ENDER-DESC.                   NC1154.2
      * L305: 030400     MOVE CCVS-E-2 TO DUMMY-RECORD. PERFORM WRITE-LINE.           NC1154.2
      * L306: 030500      IF   INSPECT-COUNTER EQUAL TO ZERO                          NC1154.2
      * L307: 030600          MOVE "NO " TO ERROR-TOTAL                               NC1154.2
      * L308: 030700      ELSE MOVE INSPECT-COUNTER TO ERROR-TOTAL.                   NC1154.2
      * L309: 030800      MOVE "TEST(S) REQUIRE INSPECTION" TO ENDER-DESC.            NC1154.2

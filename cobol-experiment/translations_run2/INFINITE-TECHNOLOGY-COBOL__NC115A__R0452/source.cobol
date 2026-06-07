      * Source excerpt from X-COBOL.
      * Attribution: INFINITE-TECHNOLOGY/COBOL; file INFINITE-TECHNOLOGY@COBOL/NC115A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L298: 029700     MOVE     CCVS-E-2 TO DUMMY-RECORD.                           NC1154.2
      * L299: 029800     PERFORM WRITE-LINE.                                          NC1154.2
      * L300: 029900 END-ROUTINE-13.                                                  NC1154.2
      * L301: 030000     IF DELETE-COUNTER IS EQUAL TO ZERO                           NC1154.2
      * L302: 030100         MOVE "NO " TO ERROR-TOTAL  ELSE                          NC1154.2
      * L303: 030200         MOVE DELETE-COUNTER TO ERROR-TOTAL.                      NC1154.2
      * L304: 030300     MOVE "TEST(S) DELETED     " TO ENDER-DESC.                   NC1154.2

      * Source excerpt from X-COBOL.
      * Attribution: INFINITE-TECHNOLOGY/COBOL; file INFINITE-TECHNOLOGY@COBOL/NC115A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L333: 033200 FAIL-ROUTINE.                                                    NC1154.2
      * L334: 033300     IF     COMPUTED-X NOT EQUAL TO SPACE                         NC1154.2
      * L335: 033400            GO TO FAIL-ROUTINE-WRITE.                             NC1154.2
      * L336: 033500     IF     CORRECT-X NOT EQUAL TO SPACE GO TO FAIL-ROUTINE-WRITE.NC1154.2
      * L337: 033600     MOVE   ANSI-REFERENCE TO INF-ANSI-REFERENCE.                 NC1154.2
      * L338: 033700     MOVE  "NO FURTHER INFORMATION, SEE PROGRAM." TO INFO-TEXT.   NC1154.2
      * L339: 033800     MOVE   XXINFO TO DUMMY-RECORD. PERFORM WRITE-LINE 2 TIMES.   NC1154.2

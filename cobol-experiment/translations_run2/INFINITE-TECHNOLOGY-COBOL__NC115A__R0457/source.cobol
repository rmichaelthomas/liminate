      * Source excerpt from X-COBOL.
      * Attribution: INFINITE-TECHNOLOGY/COBOL; file INFINITE-TECHNOLOGY@COBOL/NC115A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L347: 034600 FAIL-ROUTINE-EX. EXIT.                                           NC1154.2
      * L348: 034700 BAIL-OUT.                                                        NC1154.2
      * L349: 034800     IF     COMPUTED-A NOT EQUAL TO SPACE GO TO BAIL-OUT-WRITE.   NC1154.2
      * L350: 034900     IF     CORRECT-A EQUAL TO SPACE GO TO BAIL-OUT-EX.           NC1154.2
      * L351: 035000 BAIL-OUT-WRITE.                                                  NC1154.2
      * L352: 035100     MOVE CORRECT-A TO XXCORRECT. MOVE COMPUTED-A TO XXCOMPUTED.  NC1154.2
      * L353: 035200     MOVE   ANSI-REFERENCE TO INF-ANSI-REFERENCE.                 NC1154.2

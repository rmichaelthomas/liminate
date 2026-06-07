      * Source excerpt from X-COBOL.
      * Attribution: INFINITE-TECHNOLOGY/COBOL; file INFINITE-TECHNOLOGY@COBOL/NC115A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L331: 033000 BLANK-LINE-PRINT.                                                NC1154.2
      * L332: 033100     PERFORM WRT-LN.                                              NC1154.2
      * L333: 033200 FAIL-ROUTINE.                                                    NC1154.2
      * L334: 033300     IF     COMPUTED-X NOT EQUAL TO SPACE                         NC1154.2
      * L335: 033400            GO TO FAIL-ROUTINE-WRITE.                             NC1154.2
      * L336: 033500     IF     CORRECT-X NOT EQUAL TO SPACE GO TO FAIL-ROUTINE-WRITE.NC1154.2
      * L337: 033600     MOVE   ANSI-REFERENCE TO INF-ANSI-REFERENCE.                 NC1154.2

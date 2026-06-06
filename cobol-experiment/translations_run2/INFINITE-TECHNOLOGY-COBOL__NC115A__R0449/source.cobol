      * Source excerpt from X-COBOL.
      * Attribution: INFINITE-TECHNOLOGY/COBOL; file INFINITE-TECHNOLOGY@COBOL/NC115A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L256: 025500 DE-LETE.  MOVE "*****" TO P-OR-F.  ADD 1 TO DELETE-COUNTER.      NC1154.2
      * L257: 025600     MOVE "****TEST DELETED****" TO RE-MARK.                      NC1154.2
      * L258: 025700 PRINT-DETAIL.                                                    NC1154.2
      * L259: 025800     IF REC-CT NOT EQUAL TO ZERO                                  NC1154.2
      * L260: 025900             MOVE "." TO PARDOT-X                                 NC1154.2
      * L261: 026000             MOVE REC-CT TO DOTVALUE.                             NC1154.2
      * L262: 026100     MOVE     TEST-RESULTS TO PRINT-REC. PERFORM WRITE-LINE.      NC1154.2

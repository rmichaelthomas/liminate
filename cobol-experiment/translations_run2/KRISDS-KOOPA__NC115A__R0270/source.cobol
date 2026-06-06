      * Source excerpt from X-COBOL.
      * Attribution: krisds/koopa; file krisds@koopa/NC115A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L253: 025200 INSPT. MOVE "INSPT" TO P-OR-F. ADD 1 TO INSPECT-COUNTER.         NC1154.2
      * L254: 025300 PASS.  MOVE "PASS " TO P-OR-F.  ADD 1 TO PASS-COUNTER.           NC1154.2
      * L255: 025400 FAIL.  MOVE "FAIL*" TO P-OR-F.  ADD 1 TO ERROR-COUNTER.          NC1154.2
      * L256: 025500 DE-LETE.  MOVE "*****" TO P-OR-F.  ADD 1 TO DELETE-COUNTER.      NC1154.2
      * L257: 025600     MOVE "****TEST DELETED****" TO RE-MARK.                      NC1154.2
      * L258: 025700 PRINT-DETAIL.                                                    NC1154.2
      * L259: 025800     IF REC-CT NOT EQUAL TO ZERO                                  NC1154.2

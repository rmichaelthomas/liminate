      * Source excerpt from X-COBOL.
      * Attribution: krisds/koopa; file krisds@koopa/SQ230A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L403: 040200     PERFORM WRT-LN.                                              SQ2304.2
      * L404: 040300 FAIL-ROUTINE.                                                    SQ2304.2
      * L405: 040400     IF COMPUTED-X NOT EQUAL TO SPACE GO TO FAIL-ROUTINE-WRITE.   SQ2304.2
      * L406: 040500     IF CORRECT-X NOT EQUAL TO SPACE GO TO FAIL-ROUTINE-WRITE.    SQ2304.2
      * L407: 040600     MOVE    ANSI-REFERENCE TO INF-ANSI-REFERENCE.                SQ2304.2
      * L408: 040700     MOVE   "NO FURTHER INFORMATION, SEE PROGRAM." TO INFO-TEXT.  SQ2304.2
      * L409: 040800     MOVE    XXINFO TO DUMMY-RECORD.                              SQ2304.2

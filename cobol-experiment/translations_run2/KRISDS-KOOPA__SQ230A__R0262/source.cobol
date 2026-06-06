      * Source excerpt from X-COBOL.
      * Attribution: krisds/koopa; file krisds@koopa/SQ230A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L421: 042000     EXIT.                                                        SQ2304.2
      * L422: 042100 BAIL-OUT.                                                        SQ2304.2
      * L423: 042200     IF COMPUTED-A NOT EQUAL TO SPACE GO TO BAIL-OUT-WRITE.       SQ2304.2
      * L424: 042300     IF CORRECT-A EQUAL TO SPACE GO TO BAIL-OUT-EX.               SQ2304.2
      * L425: 042400 BAIL-OUT-WRITE.                                                  SQ2304.2
      * L426: 042500     MOVE    CORRECT-A      TO XXCORRECT.                         SQ2304.2
      * L427: 042600     MOVE    COMPUTED-A     TO XXCOMPUTED.                        SQ2304.2

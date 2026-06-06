      * Source excerpt from X-COBOL.
      * Attribution: krisds/koopa; file krisds@koopa/SQ230A.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L497: 049600*                                                                 SQ2304.2
      * L498: 049700 READ-TEST-01.                                                    SQ2304.2
      * L499: 049800     READ    SQ-FS1   AT END CONTINUE.                            SQ2304.2
      * L500: 049900     IF SQ-FS1-STATUS = "47"                                      SQ2304.2
      * L501: 050000             PERFORM PASS                                         SQ2304.2
      * L502: 050100     ELSE                                                         SQ2304.2
      * L503: 050200             MOVE "47" TO CORRECT-A                               SQ2304.2

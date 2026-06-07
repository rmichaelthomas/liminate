      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: aws-samples/aws-mainframe-modernization-carddemo; file aws-samples@aws-mainframe-modernization-carddemo/CBTRN02C.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L414:                 IF ACCT-EXPIRAION-DATE >= DALYTRAN-ORIG-TS (1:10)               
      * L415:                   CONTINUE                                                      
      * L416:                 ELSE                                                            
      * L417:                   MOVE 103 TO WS-VALIDATION-FAIL-REASON                         
      * L418:                   MOVE 'TRANSACTION RECEIVED AFTER ACCT EXPIRATION'             
      * L419:                     TO WS-VALIDATION-FAIL-REASON-DESC                           
      * L420:                 END-IF                                                          

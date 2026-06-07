      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: aws-samples/aws-mainframe-modernization-carddemo; file aws-samples@aws-mainframe-modernization-carddemo/CBTRN02C.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L403:                 COMPUTE WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT                      
      * L404:                                     - ACCT-CURR-CYC-DEBIT                       
      * L405:                                     + DALYTRAN-AMT                              
      * L406:                                                                                 
      * L407:                 IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL                             
      * L408:                   CONTINUE                                                      
      * L409:                 ELSE                                                            
      * L410:                   MOVE 102 TO WS-VALIDATION-FAIL-REASON                         
      * L411:                   MOVE 'OVERLIMIT TRANSACTION'                                  
      * L412:                     TO WS-VALIDATION-FAIL-REASON-DESC                           
      * L413:                 END-IF                                                          

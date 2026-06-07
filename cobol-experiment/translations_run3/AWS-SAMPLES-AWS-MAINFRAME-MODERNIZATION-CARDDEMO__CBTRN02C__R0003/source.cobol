      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: aws-samples/aws-mainframe-modernization-carddemo; file aws-samples@aws-mainframe-modernization-carddemo/CBTRN02C.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L545:        2800-UPDATE-ACCOUNT-REC.                                                 
      * L546:       * Update the balances in account record to reflect posted trans.          
      * L547:            ADD DALYTRAN-AMT  TO ACCT-CURR-BAL                                   
      * L548:            IF DALYTRAN-AMT >= 0                                                 
      * L549:               ADD DALYTRAN-AMT TO ACCT-CURR-CYC-CREDIT                          
      * L550:            ELSE                                                                 
      * L551:               ADD DALYTRAN-AMT TO ACCT-CURR-CYC-DEBIT                           
      * L552:            END-IF                                                               

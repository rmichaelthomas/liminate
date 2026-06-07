      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: aws-samples/aws-mainframe-modernization-carddemo; file aws-samples@aws-mainframe-modernization-carddemo/CBTRN03C.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L170:            PERFORM UNTIL END-OF-FILE = 'Y'                                      
      * L171:              IF END-OF-FILE = 'N'                                               
      * L172:                 PERFORM 1000-TRANFILE-GET-NEXT                                  
      * L173:                 IF TRAN-PROC-TS (1:10) >= WS-START-DATE                         
      * L174:                    AND TRAN-PROC-TS (1:10) <= WS-END-DATE                       
      * L175:                    CONTINUE                                                     
      * L176:                 ELSE                                                            
      * L177:                    NEXT SENTENCE                                                
      * L178:                 END-IF                                                          

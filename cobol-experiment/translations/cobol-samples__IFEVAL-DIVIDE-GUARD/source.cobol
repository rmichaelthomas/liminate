* Attribution: https://github.com/neopragma/cobol-samples
* Upstream file: cobol-samples/src/main/cobol/IFEVAL.CBL
* Excerpt lines: 77-93 (rule-bearing excerpt only; not whole file)

               ADD 1 TO NUMERIC-2 
           ELSE  
               MOVE 1 TO NUMERIC-2              
           END-IF 

      *---------------------------------------------------------------
      * Example 4: Verify a numeric item is greater than zero 
      * (This is to avoid divide-by-zero exceptions)  

           MOVE ZERO TO NUMERIC-1
           MOVE 100 TO NUMERIC-2 
           IF NUMERIC-1 IS GREATER THAN ZERO   
               DIVIDE 
                   NUMERIC-2 BY NUMERIC-1 
                   GIVING NUMERIC-2 
               END-DIVIDE     
           ELSE   

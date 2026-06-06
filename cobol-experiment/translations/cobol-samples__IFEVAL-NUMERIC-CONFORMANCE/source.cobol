* Attribution: https://github.com/neopragma/cobol-samples
* Upstream file: cobol-samples/src/main/cobol/IFEVAL.CBL
* Excerpt lines: 65-75 (rule-bearing excerpt only; not whole file)

           IF ALPHA-1 IS EQUAL TO 'foobar'    
               MOVE 'equal' TO RESULT-OF-COMPARE    
           ELSE    
               MOVE 'different' TO RESULT-OF-COMPARE  
           END-IF 

      *---------------------------------------------------------------
      * Example 3: Verify a numeric item contains numeric data 
      * (This is to avoid a Data Exception or S0C7 runtime error)

           MOVE 'garbage' TO NUMERIC-2-X    

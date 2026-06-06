* Attribution: https://github.com/neopragma/cobol-samples
* Upstream file: cobol-samples/src/main/cobol/IFEVAL.CBL
* Excerpt lines: 119-144 (rule-bearing excerpt only; not whole file)

                  MOVE 'numeric-1' TO RESULT-OF-COMPARE   
               WHEN NUMERIC-1 < NUMERIC-2 
                  MOVE 'numeric-2' TO RESULT-OF-COMPARE    
               WHEN OTHER
                  MOVE 'equal' TO RESULT-OF-COMPARE
           END-EVALUATE

      *---------------------------------------------------------------
      * Example 6: EVALUATE statement, two conditions  

           MOVE 8 TO NUMERIC-1  
           MOVE 13 TO NUMERIC-2 
           MOVE 'THX-1138' TO ALPHA-1    
           MOVE 'Terminator' TO ALPHA-2 

           EVALUATE TRUE ALSO TRUE 
               WHEN NUMERIC-1 IS GREATER THAN NUMERIC-2 
               ALSO ALPHA-1(1:3) EQUAL 'THX'
                  MOVE 'THX and numeric-1' TO RESULT-OF-COMPARE   
               WHEN NUMERIC-1 < NUMERIC-2 
               ALSO ALPHA-1(1:3) EQUAL 'THX'
                  MOVE 'THX and numeric-2' TO RESULT-OF-COMPARE 
               WHEN NUMERIC-1 = NUMERIC-1 
               ALSO ALPHA-2 = 'Terminator'
                  MOVE 'Terminator and equal numbers' 
                      TO RESULT-OF-COMPARE      

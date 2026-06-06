* Attribution: https://github.com/neopragma/cobol-samples
* Upstream file: cobol-samples/src/main/cobol/NOTBOOL.CBL
* Excerpt lines: 65-168 (rule-bearing excerpt only; not whole file)

      * PIC X where 'T' = true and SPACE = false 

      * Set the flag
           MOVE EX2-TRUE-VALUE TO EX2-FLAG 

      * Test the flag
           IF EX2-FLAG EQUAL EX2-TRUE-VALUE 
               MOVE 'true' TO THE-ANSWER 
           ELSE 
               MOVE 'false' TO THE-ANSWER 
           END-IF         

      * Toggle the flag 
           IF EX2-FLAG EQUAL EX2-TRUE-VALUE 
               MOVE SPACE TO EX2-FLAG 
           ELSE  
               MOVE EX2-TRUE-VALUE TO EX2-FLAG 
           END-IF         

      *----------------------------------------------------------------
      * Example 3: Pseudo-boolean based on a coding convention 
      * PIC X where 'Y' = yes and 'N' = no 

      * Set the flag
           MOVE EX3-YES-VALUE TO EX3-FLAG 

      * Test the flag
           IF EX3-FLAG EQUAL EX3-YES-VALUE 
               MOVE 'yes' TO THE-ANSWER 
           ELSE 
               MOVE 'no' TO THE-ANSWER 
           END-IF         

      * Another coding style:

           if ex3-flag not equal ex3-yes-value 
               move 'no' to the-answer.

      * Toggle the flag 
           IF EX3-FLAG EQUAL EX3-YES-VALUE 
               MOVE 'N' TO EX3-FLAG 
           ELSE          
               MOVE EX3-YES-VALUE TO EX3-FLAG 
           END-IF 

      *----------------------------------------------------------------
      * Example 4: Pseudo-boolean based on a coding convention 
      * PIC X where '1' = true and '0' = false 

      * Set the flag
           MOVE EX4-TRUE-VALUE TO EX4-FLAG 

      * Test the flag
           EVALUATE TRUE
               WHEN EX4-FLAG EQUAL EX4-TRUE-VALUE
                  MOVE 'true' TO THE-ANSWER 
               WHEN EX4-FLAG EQUAL EX4-FALSE-VALUE   
                  MOVE 'false' TO THE-ANSWER  
               WHEN OTHER
                  MOVE 'not set' TO THE-ANSWER
           END-EVALUATE

      * Toggle the flag 
           IF EX4-FLAG EQUAL EX4-TRUE-VALUE 
               MOVE EX4-FALSE-VALUE TO EX4-FLAG 
           ELSE 
               MOVE EX4-TRUE-VALUE TO EX4-FLAG 
           END-IF 

      *----------------------------------------------------------------
      * Example 5: Pseudo-boolean using 88-level items without FALSE

      * Set the flag 
           SET EX5-FLAG TO TRUE 

      * Test the flag 
           if Ex5-Flag 
               move 'true' to The-Answer 
           end-if    
      
      * Toggle the flag 
           IF EX5-FLAG  
               MOVE SPACE TO EX5-FIELD 
           ELSE     
               SET EX5-FLAG TO TRUE
           END-IF 

      *----------------------------------------------------------------
      * Example 6: Pseudo-boolean using 88-level items with FALSE

      * Set the flag 
           SET EX6-FLAG TO TRUE 

      * Test the flag 
           if Ex6-Flag 
               move 'true' to The-Answer 
           end-if    
      
      * Toggle the flag 
           IF EX6-FLAG  
               SET EX6-FLAG TO FALSE 
           ELSE     
               SET EX5-FLAG TO TRUE
           END-IF 

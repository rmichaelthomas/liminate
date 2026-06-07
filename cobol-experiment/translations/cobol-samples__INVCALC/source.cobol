* Attribution: https://github.com/neopragma/cobol-samples
* Upstream file: cobol-samples/src/main/cobol/INVCALC.CBL
* Excerpt lines: 84-125 (rule-bearing excerpt only; not whole file)

                    
           PERFORM WITH TEST BEFORE 
                   VARYING WORKING-INDEX 
                   FROM 1 BY 1 
                   UNTIL WORKING-INDEX > INV-LINE-ITEM-COUNT 
               IF INV-LINE-QUANTITY(WORKING-INDEX) IS NUMERIC 
               AND INV-LINE-UNIT-PRICE(WORKING-INDEX) IS NUMERIC 
                   MOVE ZERO 
                       TO LINE-WORKING-TOTAL 
                          LINE-WORKING-TAX
                   MULTIPLY 
                       INV-LINE-QUANTITY(WORKING-INDEX) 
                       BY INV-LINE-UNIT-PRICE(WORKING-INDEX) 
                       GIVING LINE-WORKING-TOTAL 
                   END-MULTIPLY 
                   ADD LINE-WORKING-TOTAL 
                       TO CUMULATIVE-PRICE-BEFORE-TAX
                   END-ADD    
                   IF TAXABLE-ITEM(WORKING-INDEX) 
                       MULTIPLY LINE-WORKING-TOTAL
                           BY SALES-TAX-RATE 
                           GIVING LINE-WORKING-TAX
                       END-MULTIPLY 
                       ADD LINE-WORKING-TAX 
                           TO LINE-WORKING-TOTAL    
                   END-IF  
                   ADD LINE-WORKING-TOTAL 
                       TO CUMULATIVE-PRICE-WITH-TAX
                   END-ADD     
                   ADD LINE-WORKING-TAX 
                       TO CUMULATIVE-SALES-TAX    
                   END-ADD            
               ELSE 
                   PERFORM INVALID-INVOICE-DATA 
               END-IF 
           END-PERFORM                     

           MOVE CUMULATIVE-SALES-TAX TO INV-TOTAL-SALES-TAX 
           MOVE CUMULATIVE-PRICE-BEFORE-TAX  TO INV-TOTAL-BEFORE-TAX 
           MOVE CUMULATIVE-PRICE-WITH-TAX TO INV-TOTAL-AMOUNT 

           PERFORM PRINT-INVOICE-DETAILS

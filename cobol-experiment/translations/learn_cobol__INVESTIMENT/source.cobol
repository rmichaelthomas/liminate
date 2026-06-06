* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/INVESTIMENT.cobol
* Excerpt lines: 24-46 (rule-bearing excerpt only; not whole file)

      *  calculate interest
           MULTIPLY amount-start BY rate-of-interest 
                 GIVING temp ROUNDED 
           DIVIDE temp BY 100 GIVING  interest ROUNDED 
                                 interest-out ROUNDED    
               ON SIZE ERROR
      *        error message and go no further
                  DISPLAY "Interest too large"
               NOT ON SIZE ERROR
      *        calculate new amount
                 ADD interest, amount-start 
                       GIVING amount-end-out ROUNDED 
                     ON SIZE ERROR
      *              error message and go no further
                       DISPLAY "Final Amount too large"
                     NOT on SIZE ERROR
      *              display results
                       MOVE amount-start  TO amount-start-out 
                       DISPLAY "Start Amount " amount-start-out 
                       DISPLAY  "Interest " interest-out 
                       DISPLAY "Final Amount " amount-end-out 
                  END-ADD
           END-DIVIDE

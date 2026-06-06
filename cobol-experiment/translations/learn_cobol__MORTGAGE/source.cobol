* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/MORTGAGE.cobol
* Excerpt lines: 33-45 (rule-bearing excerpt only; not whole file)

           ACCEPT repayment  
           DISPLAY "Enter Monthly Interest Rate: " WITH NO ADVANCING 
           ACCEPT interest-rate 
           .
       
       Calculate-interest.
           COMPUTE interest = (balance-start * interest-rate ) / 100
           COMPUTE balance-end = balance-start  + interest 
                                   - (12 * repayment )
           MOVE balance-start  TO balance-start-out 
           MOVE interest TO interest-out
           MOVE balance-end TO balance-end-out 
           DISPLAY balance-start-out " "

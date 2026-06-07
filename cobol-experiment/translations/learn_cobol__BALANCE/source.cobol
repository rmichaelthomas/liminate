* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/BALANCE.cobol
* Excerpt lines: 12-18 (rule-bearing excerpt only; not whole file)

           DISPLAY "Enter old balance: " WITH NO ADVANCING 
           ACCEPT old-balance 
           DISPLAY "Enter amount   :" WITH NO ADVANCING 
           ACCEPT amount 
           ADD amount, old-balance GIVING new-balance 
           DISPLAY "New balance: " new-balance


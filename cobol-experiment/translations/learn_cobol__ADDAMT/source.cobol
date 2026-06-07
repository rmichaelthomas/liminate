* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/ADDAMT.cobol
* Excerpt lines: 26-33 (rule-bearing excerpt only; not whole file)

               ACCEPT AMT2-IN
               DISPLAY 'Enter amount of third purchase (5 digits)'
               ACCEPT AMT3-IN
               MOVE CUST-NO-IN TO CUST-NO-OUT
               ADD AMT1-IN  AMT2-IN  AMT3-IN
                   GIVING TOTAL-OUT
               DISPLAY CUST-NO-OUT 'Total Amount = ' TOTAL-OUT
               DISPLAY 'MORE INPUT DATA (YES/NO)?'

* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/NET-PAY.cobol
* Excerpt lines: 18-28 (rule-bearing excerpt only; not whole file)

           DISPLAY "Enter National Insurance : " WITH NO ADVANCING 
           ACCEPT nssf 

           SUBTRACT tax, annual-pay , nssf FROM gross-pay 
                    GIVING net-pay ROUNDED 
              ON SIZE ERROR
                    DISPLAY "Error in data sizes"
              NOT ON SIZE ERROR
                    DISPLAY "Net pay is " net-pay 
                    
           END-SUBTRACT

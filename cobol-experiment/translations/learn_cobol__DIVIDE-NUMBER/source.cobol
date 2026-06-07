* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/DIVIDE-NUMBER.cobol
* Excerpt lines: 15-25 (rule-bearing excerpt only; not whole file)

           ACCEPT divisor 
           
           DIVIDE dividend BY divisor 
              GIVING quotient REMAINDER remains
              ON SIZE ERROR
                 MOVE ZERO TO quotient, remains 
                 DISPLAY "An error occured"
              NOT ON SIZE ERROR
                 DISPLAY dividend " / "  divisor " = " quotient
                    " remainder " remains
           END-DIVIDE

* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/ADD-WITH-SIZE-ERROR.cobol
* Excerpt lines: 18-29 (rule-bearing excerpt only; not whole file)

           ACCEPT in-2
           DISPLAY SPACES
           ADD in-1 TO in-2 GIVING result-1 ROUNDED
              ON SIZE ERROR
                 DISPLAY "result too large"
                 MOVE ZERO TO result-1
               NOT ON SIZE ERROR
                 MOVE in-1 TO out-1
                 MOVE in-2 TO out-2
                 DISPLAY out-1 " + " out-2 " = "
                         result-1 " (to 1 dec p1) "
           END-ADD

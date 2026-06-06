* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/TIME-AND-DATE.cobol
* Excerpt lines: 28-39 (rule-bearing excerpt only; not whole file)

           ACCEPT time-today FROM TIME
      * format date for output
           MOVE date-in-dd  TO date-out-dd 
           MOVE date-in-mm  TO date-out-mm  
           MOVE date-in-yy  TO date-out-yy 
          
           IF date-in-yy < 96
              MOVE 20 TO date-out-cc 
           ELSE
              MOVE 19 TO date-out-cc
           END-IF
           DISPLAY "Today's date is:" date-out-format 

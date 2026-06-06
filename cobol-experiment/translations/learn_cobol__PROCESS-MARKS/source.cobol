* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/PROCESS-MARKS.cobol
* Excerpt lines: 24-33 (rule-bearing excerpt only; not whole file)

       
       calculate-grade.

           EVALUATE (english-marks + math-marks) /2
              WHEN 40 THRU 49.9 DISPLAY "Third Class"
              WHEN 50 THRU 59.9 DISPLAY "Lower Class"
              WHEN 60 THRU 69.9 DISPLAY "Upper Class"
              WHEN 70 THRU 100  DISPLAY "First Class"
              WHEN OTHER        DISPLAY "Prog or Data Error!"
           END-EVALUATE.

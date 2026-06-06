* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/AGE-CHECK.cobol
* Excerpt lines: 13-20 (rule-bearing excerpt only; not whole file)

           ACCEPT your-name
           DISPLAY  "Type in your age"
           ACCEPT age 
           IF age > 21
              DISPLAY your-name " is over 21"
           ELSE
              DISPLAY your-name " is 21 or under"
           END-IF 

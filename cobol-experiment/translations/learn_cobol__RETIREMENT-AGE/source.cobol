* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/RETIREMENT-AGE.cobol
* Excerpt lines: 5-32 (rule-bearing excerpt only; not whole file)

       WORKING-STORAGE SECTION. 
       01  gender      PIC X.
           88  male    VALUE "M".
           88  female  VALUE "F".

           
       01  age         PIC 99 PACKED-DECIMAL.

       PROCEDURE DIVISION.
       BEGIN.
           DISPLAY "RETIREMENT AGE PROGRAM"
           PERFORM get-input
           PERFORM process-retirement
           GOBACK .

       get-input.
           DISPLAY "Enter your gender: M for Male and F for Female : "
           WITH NO ADVANCING 
           ACCEPT gender 
           DISPLAY "Enter your age 1 to 120:  " WITH NO ADVANCING 
           ACCEPT age.
       
       process-retirement.
           IF female AND age >= 60 OR male AND age >= 65
              DISPLAY "RETIREMENT AGE"
           ELSE
              DISPLAY "NOT RETIREMENT AGE"
           END-IF.

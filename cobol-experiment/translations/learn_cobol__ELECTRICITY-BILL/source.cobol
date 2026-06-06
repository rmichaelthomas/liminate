* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/ELECTRICITY-BILL.cobol
* Excerpt lines: 6-47 (rule-bearing excerpt only; not whole file)

       01  input-values.
           03   present-reading   PIC 99999.
           03   previous-reading  PIC 99999.
       01  fixed-values.
           03 basic-units         PIC 999 VALUE 72.
           03 basic-rate          PIC 9V999 VALUE 0.035.
           03 cheap-rate          PIC 9V999 VALUE 0.009.
           03 standing-charge     PIC 9V999 VALUE 2.50.
           03 vat                 PIC 9V999 VALUE 0.08.
             
       01 calculated-values.
           03 units               PIC S99999.
           03 charge              PIC 999999V99.
           03 charge-out          PIC $$$$$$9.99.


       PROCEDURE DIVISION.
       calculate-bill.
           DISPLAY "ELECTRICITY BILL PROGRAM"
      * get input     
           DISPLAY  "Enter present reading: " WITH NO ADVANCING
           ACCEPT present-reading
           DISPLAY "Enter previous reading: " WITH NO ADVANCING
           ACCEPT previous-reading
        

      * compute bill
           COMPUTE units = present-reading  -previous-reading
           IF units NEGATIVE
              DISPLAY "ERROR! Units are negative"
           ELSE
              IF units >  basic-units
                 COMPUTE charge ROUNDED = basic-units * basic-rate + 
                     ((units - basic-units) * cheap-rate)
              ELSE
                 COMPUTE charge ROUNDED = basic-rate * units
              END-IF
              COMPUTE charge-out = (1 + vat ) * 
                       (charge + standing-charge)
    
               DISPLAY "CHARGE is " charge-out
           END-IF

* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/SHOPPING-BILL.cobol
* Excerpt lines: 12-18 (rule-bearing excerpt only; not whole file)

           MOVE ZERO TO total-bill
           DISPLAY "Enter Cost of Items (zero to end"
           ACCEPT item-cost
           PERFORM UNTIL item-cost  = ZERO
              ADD item-cost TO total-bill ROUNDED
              ACCEPT item-cost
           END-PERFORM

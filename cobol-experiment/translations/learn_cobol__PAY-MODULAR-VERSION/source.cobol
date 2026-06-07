* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/PAY-MODULAR-VERSION.cobol
* Excerpt lines: 28-37 (rule-bearing excerpt only; not whole file)

           ACCEPT rate-of-pay .

       Pay-Calculation.
           IF hours-worked  > std-hours 
              COMPUTE pay ROUNDED  = std-hours * rate-of-pay 
                                      + 1.5 * rate-of-pay 
                                      + (hours-worked  - std-hours)
           ELSE
              COMPUTE pay ROUNDED = hours-worked * rate-of-pay
           END-IF .

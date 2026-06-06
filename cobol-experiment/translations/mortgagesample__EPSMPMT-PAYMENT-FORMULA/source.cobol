* Attribution: https://github.com/rradclif/mortgagesample
* Upstream file: mortgagesample/MortgageApplication/cobol/epsmpmt.cbl
* Excerpt lines: 120-141 (rule-bearing excerpt only; not whole file)

           COMPUTE WS-CALC-INTEREST =
                              (EPSPDATA-QUOTED-INTEREST-RATE / 100) / 12
           .

       A200-CALULATE-MONTH-PAYMENT.
           COMPUTE EPSPDATA-RETURN-MONTH-PAYMENT
                   = EPSPDATA-PRINCIPLE-DATA *
                     (WS-CALC-INTEREST *
                     (1 + WS-CALC-INTEREST) ** WS-NUMBER-OF-MONTHS) /
                     (((1 + WS-CALC-INTEREST )
                                            ** WS-NUMBER-OF-MONTHS) - 1)
           .
      *     DISPLAY 'RETURN PAYMENT = ' EPSPDATA-RETURN-MONTH-PAYMENT.
      *     COMPUTE C = WS-CALC-INTEREST.
      *     COMPUTE N = WS-NUMBER-OF-MONTHS.
      *     COMPUTE L = EPSPDATA-PRINCIPLE-DATA.
      *     COMPUTE P = L * (C * (1 + C ) ** N)/(((1 + C) ** N) - 1).


      * DEAD CODE USED FOR TESTING
       A300-TRY2.
           MOVE EPSPDATA-PRINCIPLE-DATA TO Loan.

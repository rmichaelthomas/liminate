* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/COMPOUND-INTEREST.cobol
* Excerpt lines: 23-31 (rule-bearing excerpt only; not whole file)


           COMPUTE amount-at-end ROUNDED = amount *
                          (1 + rate-of-interest / 100) ** years
                 ON SIZE ERROR
                    DISPLAY "amount too large"
                 NOT ON SIZE ERROR
                    DISPLAY "Final Amount " amount-at-end

           END-COMPUTE

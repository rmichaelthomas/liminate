* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/COST.cobol
* Excerpt lines: 14-21 (rule-bearing excerpt only; not whole file)

       Cost-calc .
           DISPLAY "Enter price: " WITH NO ADVANCING
           ACCEPT price
           DISPLAY "Enter vat : " WITH NO ADVANCING
           ACCEPT vat

           ADD vat , price GIVING cost-out
           MOVE price TO price-out

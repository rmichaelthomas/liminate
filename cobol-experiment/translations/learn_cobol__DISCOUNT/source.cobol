* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/DISCOUNT.cobol
* Excerpt lines: 10-17 (rule-bearing excerpt only; not whole file)

           DISPLAY " Enter charge : " WITH NO ADVANCING
           ACCEPT charge
           DISPLAY " Enter discount : " WITH NO ADVANCING
           ACCEPT discount           
           SUBTRACT discount FROM charge
               GIVING discounted-charge ROUNDED 
           DISPLAY SPACES
           DISPLAY "Discounted Charge: " discounted-charge

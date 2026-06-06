* Attribution: https://github.com/kalsmic/learn_cobol
* Upstream file: learn_cobol/WORD-ORDER.cobol
* Excerpt lines: 11-20 (rule-bearing excerpt only; not whole file)

           ACCEPT word-1
           DISPLAY "Enter 2nd word: " WITH NO ADVANCING
           ACCEPT word-2

           IF word-1 < word-2
              DISPLAY word-1 " comes before " word-2
           ELSE
              DISPLAY word-2 " comes before " word-1
           END-IF
           STOP RUN.

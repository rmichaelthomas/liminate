* Attribution: https://github.com/rradclif/mortgagesample
* Upstream file: mortgagesample/MortgageApplication/cobol_cics/epscsmrd.cbl
* Excerpt lines: 3877-3904 (rule-bearing excerpt only; not whole file)

           COMPUTE CMP-TMPA
            = CONTENT-LEN - (CONTENT-TXT-NDX - 1)
           IF CMP-TMPA > 0 AND
              CONTENT-TXT(CONTENT-TXT-NDX:1) = '0'
            INITIALIZE CMP-TMPB
            INSPECT CONTENT-TXT(CONTENT-TXT-NDX:CMP-TMPA)
             TALLYING CMP-TMPB FOR LEADING '0'
            IF CMP-TMPB > 0
             COMPUTE CMP-TMPA
              = CONTENT-TXT-NDX + CMP-TMPB
             IF CONTENT-TXT(CMP-TMPA:1) = '.'
              SUBTRACT 1 FROM CMP-TMPB
             END-IF
             ADD CMP-TMPB TO CONTENT-TXT-NDX
            END-IF
           END-IF
           COMPUTE CMP-TMPA
            = CONTENT-LEN - (CONTENT-TXT-NDX - 1)
           IF CMP-TMPA > 0
            MOVE CONTENT-TXT(CONTENT-TXT-NDX:CMP-TMPA)
              TO CONTENT-BUF(CONTENT-BUF-NDX:CMP-TMPA)
            ADD  CMP-TMPA TO CONTENT-BUF-NDX
           END-IF
           COMPUTE CONTENT-LEN = CONTENT-BUF-NDX - 1
           IF CONTENT-LEN > 0
            MOVE CONTENT-BUF(1:CONTENT-LEN)
              TO CONTENT-TXT(1:CONTENT-LEN)
           END-IF

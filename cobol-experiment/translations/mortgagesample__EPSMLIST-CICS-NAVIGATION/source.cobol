* Attribution: https://github.com/rradclif/mortgagesample
* Upstream file: mortgagesample/MortgageApplication/cobol/epsmlist.cbl
* Excerpt lines: 95-115 (rule-bearing excerpt only; not whole file)

           EVALUATE TRUE
               WHEN EIBCALEN = ZERO
      * First time in - Show Screen
                   PERFORM A100-PROCESS-MAP
               WHEN EIBAID = DFHCLEAR
      * Process CLEAR key
                   EXEC CICS
                        RETURN
                   END-EXEC
               WHEN EIBAID = DFHPF3 OR DFHPF12
      * Process END/RETURN keys
                   EXEC CICS
                        RETURN
                   END-EXEC
               WHEN EIBAID = DFHENTER
      * Process ENTER Key
                   PERFORM A100-PROCESS-MAP
               WHEN OTHER
      * Present Invalid Key
                   PERFORM A100-PROCESS-MAP
           END-EVALUATE

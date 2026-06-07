* Attribution: https://github.com/rradclif/mortgagesample
* Upstream file: mortgagesample/MortgageApplication/cobol_cics_db2/epscmort.cbl
* Excerpt lines: 80-141 (rule-bearing excerpt only; not whole file)

           EVALUATE TRUE
               WHEN EIBCALEN = ZERO
      * First time in - Show Screen
                   MOVE LOW-VALUES TO EPMENUO
                   SET SEND-ERASE TO TRUE
                   PERFORM A300-SEND-MAP
                   MOVE '3' TO
                      PROCESS-INDICATOR OF W-COMMUNICATION-AREA
               WHEN EIBAID = DFHCLEAR
      * Process CLEAR key
                   MOVE LOW-VALUES TO EPMENUO
                   SET SEND-ERASE TO TRUE
                   PERFORM A300-SEND-MAP
               WHEN EIBAID = DFHPF3 OR DFHPF12
      * Process END/RETURN keys
                  IF PROCESS-INDICATOR OF W-COMMUNICATION-AREA = '3'
                      EXEC CICS
                         SEND TEXT FROM (END-OF-TRANS-MSG)
                         ERASE
                         FREEKB
                      END-EXEC
                      EXEC CICS
                           RETURN
                      END-EXEC
                   ELSE
                      SET SEND-ALL TO TRUE
                      EXEC CICS
                         SEND TEXT FROM (BLANK-MSG)
                         ERASE
                         FREEKB
                      END-EXEC
                      PERFORM A300-SEND-MAP
                      MOVE '3' TO
                          PROCESS-INDICATOR OF W-COMMUNICATION-AREA
                   END-IF
               WHEN EIBAID = DFHPF9
                   MOVE '9' TO
                      PROCESS-INDICATOR OF W-COMMUNICATION-AREA
                   EXEC CICS LINK PROGRAM( 'EPSMLIST' )
                          COMMAREA( W-COMMUNICATION-AREA )
                   END-EXEC
               WHEN EIBAID = DFHENTER
      * Process ENTER Key
                   IF PROCESS-INDICATOR OF W-COMMUNICATION-AREA = '3'
                      PERFORM A100-PROCESS-MAP
                   ELSE
                      EXEC CICS LINK PROGRAM('EPSMLIST')
                             COMMAREA( W-COMMUNICATION-AREA )
                      END-EXEC
                   END-IF
               WHEN OTHER
      * Process Data
                    IF PROCESS-INDICATOR OF W-COMMUNICATION-AREA = '3'
                      PERFORM A600-CALCULATE-MORTGAGE
                      EXEC CICS RETURN END-EXEC
      *             ELSE
      *                MOVE X'E8' TO MSGERRA
      *                MOVE LOW-VALUES TO EPMENUO
      *                SET SEND-DATAONLY-ALARM TO TRUE
      *                PERFORM A300-SEND-MAP
                    END-IF
           END-EVALUATE

* Attribution: https://github.com/rradclif/mortgagesample
* Upstream file: mortgagesample/MortgageApplication/cobol/epsnbrvl.cbl
* Excerpt lines: 83-185 (rule-bearing excerpt only; not whole file)

           IF WS-IDX > WS-MAX-FIELD
              MOVE WS-MAX-FIELD TO WS-IDX
           ELSE
              MOVE WS-IDX       TO WS-MAX-FIELD
           END-IF.

           MOVE ZERO   TO WS-END-SPACE.
           MOVE SPACES TO EPSPARM-RETURN-ERROR.
           MOVE ZERO   TO EPSPARM-BINARY-NUMBER
                          EPSPARM-NUMBER
                          EPSPARM-DECIMAL.

      * FIND TRAILING SPACES
           PERFORM UNTIL WS-IDX = 0
              IF EPSPARM-VALIDATE-DATA(WS-IDX:1) = SPACES
                ADD 1      TO WS-TRAILING-SPACES
                SUBTRACT 1 FROM WS-IDX
              ELSE
                MOVE WS-IDX TO WS-END-SPACE
                MOVE 0 TO WS-IDX
              END-IF
           END-PERFORM.

      * FIND LEADING SPACES
           MOVE 1 TO WS-LEADING-SPACES.

           IF WS-END-SPACE NOT = 0
              MOVE 1 TO WS-IDX
              PERFORM UNTIL WS-IDX >= WS-END-SPACE
                IF EPSPARM-VALIDATE-DATA(WS-IDX:1) = SPACES
                   ADD 1 TO WS-LEADING-SPACES
                   ADD 1 TO WS-IDX
                ELSE
                   COMPUTE WS-IDX = WS-END-SPACE + 1
                END-IF
              END-PERFORM
           ELSE
              MOVE STATIC-ERROR-TABLE(1) TO EPSPARM-RETURN-ERROR
           END-IF.

           MOVE WS-LEADING-SPACES TO WS-IDX.
           MOVE 1                 TO WS-DEC-IDX.
           MOVE 0                 TO WS-DECIMAL-SPACE.

      * FIND DECIMAL POINT
           PERFORM A002-COMPUTE-DECIMAL
                   UNTIL WS-IDX > WS-END-SPACE
           .

           IF WS-DECIMAL-SPACE > 0
              COMPUTE WS-END-SPACE = WS-DECIMAL-SPACE - 1
           END-IF.

      * VALIDATE NO INTERNAL BLANKS
           MOVE WS-END-SPACE             TO WS-IDX.
           MOVE LENGTH OF EPSPARM-NUMBER TO WS-NUM-IDX.
      *     SUBTRACT 1 FROM WS-NUM-IDX.

           PERFORM A001-COMPUTE-INTEGER
                   UNTIL WS-IDX < WS-LEADING-SPACES
           .

           IF EPSPARM-RETURN-ERROR = SPACES
              COMPUTE EPSPARM-BINARY-NUMBER = EPSPARM-NUMBER
                                            + EPSPARM-DECIMAL
           END-IF.
           GOBACK
           .

       A001-COMPUTE-INTEGER.
           IF EPSPARM-VALIDATE-DATA(WS-IDX:1) = ','
              SUBTRACT 1 FROM WS-IDX
           ELSE
              IF EPSPARM-VALIDATE-DATA(WS-IDX:1) = SPACE
              OR EPSPARM-VALIDATE-DATA(WS-IDX:1) IS NOT NUMERIC
                 MOVE STATIC-ERROR-TABLE(2) TO EPSPARM-RETURN-ERROR
                 MOVE 0 TO WS-IDX
              ELSE
                 MOVE EPSPARM-VALIDATE-DATA(WS-IDX:1) TO
                      EPSPARM-NUMBER(WS-NUM-IDX:1)
                 SUBTRACT 1 FROM WS-IDX
                                 WS-NUM-IDX
              END-IF
           END-IF
           .

       A002-COMPUTE-DECIMAL.
           IF WS-DECIMAL-SPACE = 0
              IF EPSPARM-VALIDATE-DATA(WS-IDX:1) = '.'
                 MOVE WS-IDX TO WS-DECIMAL-SPACE
              END-IF
           ELSE
              IF EPSPARM-VALIDATE-DATA(WS-IDX:1) = '.'
                 MOVE STATIC-ERROR-TABLE(3) TO EPSPARM-RETURN-ERROR
                 MOVE WS-END-SPACE TO WS-IDX
                 MOVE 1            TO WS-DEC-IDX
              ELSE
                 MOVE EPSPARM-VALIDATE-DATA(WS-IDX:1) TO
                      EPSPARM-DECIMAL(WS-DEC-IDX:1)
                 ADD 1 TO WS-DEC-IDX
              END-IF
           END-IF
           ADD 1 TO WS-IDX

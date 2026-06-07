* Attribution: https://github.com/rradclif/mortgagesample
* Upstream file: mortgagesample/MortgageApplication/cobol/epsmpmt.cbl
* Excerpt lines: 26-117 (rule-bearing excerpt only; not whole file)

           03 STATIC-MAXIMUM-PRINCIPLE    PIC 9(9)V99
                                VALUE 100000000.01.
           03 STATIC-ERRORS.
              05 FILLER                  PIC 99 VALUE 1.
              05 FILLER                  PIC X(80)
              VALUE 'PRINCIPLE AMOUNT IS NEGATIVE'.
              05 FILLER                  PIC 99 VALUE 2.
              05 FILLER                  PIC X(80)
              VALUE 'PRINCIPLE EXCEEDED MAXIMUM AMOUNT'.
              05 FILLER                  PIC 99 VALUE 3.
              05 FILLER                  PIC X(80)
              VALUE 'NEGATIVE INTEREST RATE'.
              05 FILLER                  PIC 99 VALUE 4.
              05 FILLER                  PIC X(80)
              VALUE 'YEARS INDICATED, BUT YEARS ZERO OR LESS'.
              05 FILLER                  PIC 99 VALUE 5.
              05 FILLER                  PIC X(80)
              VALUE 'ZERO OR LESS MONTHS'.
              05 FILLER                  PIC 99 VALUE 6.
              05 FILLER                  PIC X(80)
              VALUE ' '.
              05 FILLER                  PIC 99 VALUE 7.
              05 FILLER                  PIC X(80)
              VALUE ' '.
              05 FILLER                  PIC 99 VALUE 8.
              05 FILLER                  PIC X(80)
              VALUE ' '.
              05 FILLER                  PIC 99 VALUE 9.
              05 FILLER                  PIC X(80)
              VALUE ' '.
              05 FILLER                  PIC 99 VALUE 10.
              05 FILLER                  PIC X(80)
              VALUE ' '.
           03 STATIC-ERROR-TBL REDEFINES STATIC-ERRORS.
              05 STATIC-ERROR-TABLE OCCURS 10 TIMES.
                07 ERROR-INDICATOR         PIC 99.
                07 ERROR-TEXT              PIC X(80).
       01  WS-INDICATORS-AND-FLAGS.
           03 VALIDATION-INDICATOR   PIC 9.
       01  WS-WORK-AMOUNTS.
           03 WS-NUMBER-OF-MONTHS    PIC 9(9)V99   COMP.
           03 WS-CALC-INTEREST       COMP-1.
      *     03 L                      COMP-1.
      *     03 C                      COMP-1.
      *     03 N                      PIC S9(5) COMP.
      *     03 P                      COMP-1.
       01  Loan             Pic 9(9)V99.
       01  Payment          Pic 9(9)V99.
       01  Interest         Pic 9(9)V9999.
       01  Number-Periods   Pic 999.
      *
       LINKAGE SECTION.
      *
       COPY EPSPDATA.

       PROCEDURE DIVISION USING EPSPDATA.
      *
       A000-MAINLINE.
           MOVE 0 TO VALIDATION-INDICATOR.
           MOVE 0 TO WS-NUMBER-OF-MONTHS.
           PERFORM A100-VALIDATE-INPUT.
           IF VALIDATION-INDICATOR = 0
              PERFORM A200-CALULATE-MONTH-PAYMENT
      *        PERFORM A300-TRY2
           ELSE
              PERFORM A999-RETURN-ERROR-TEXT
           END-IF.
           GOBACK
           .
      *
       A100-VALIDATE-INPUT.
           MOVE SPACES TO EPSPDATA-RETURN-ERROR.
           IF EPSPDATA-PRINCIPLE-DATA > 0
              IF EPSPDATA-PRINCIPLE-DATA > STATIC-MAXIMUM-PRINCIPLE
                 MOVE 2 TO VALIDATION-INDICATOR
              END-IF
           ELSE
              MOVE 1 TO VALIDATION-INDICATOR
           END-IF
           .
           IF VALIDATION-INDICATOR = 0
              IF EPSPDATA-QUOTED-INTEREST-RATE <= 0
                 MOVE 3 TO VALIDATION-INDICATOR
              ELSE
                 IF EPSPDATA-YEAR-MONTH-IND = 'Y'
                    COMPUTE WS-NUMBER-OF-MONTHS =
                               EPSPDATA-NUMBER-OF-YEARS * 12
                 ELSE
                    MOVE EPSPDATA-NUMBER-OF-MONTHS TO
                            WS-NUMBER-OF-MONTHS
                 END-IF
              END-IF

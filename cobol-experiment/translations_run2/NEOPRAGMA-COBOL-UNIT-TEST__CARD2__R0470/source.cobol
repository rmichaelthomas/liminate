      * Source excerpt from X-COBOL.
      * Attribution: neopragma/cobol-unit-test; file neopragma@cobol-unit-test/CARD2.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L40:                AND IN-ACCOUNT-NUMBER(1:2) IS < '56'
      * L41:                    MOVE 'MASTERCARD' TO WS-CARD-TYPE
      * L42:                WHEN IN-ACCOUNT-NUMBER(1:2) = '36'
      * L43:                WHEN IN-ACCOUNT-NUMBER(1:2) = '38'
      * L44:                    MOVE 'DINERS CLUB' TO WS-CARD-TYPE
      * L45:                WHEN IN-ACCOUNT-NUMBER(1:4) = '6011'
      * L46:                WHEN IN-ACCOUNT-NUMBER(1:2) = '65'

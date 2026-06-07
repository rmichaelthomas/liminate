      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: javiertello/UnizarBank; file javiertello@UnizarBank/TRANSFER.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L124:        COMPROBAR.
      * L125:            DIVIDE CENTIMOS BY 100 GIVING CANTOT.
      * L126:            ADD EUROS TO CANTOT GIVING CANTOT.
      * L127:            IF CANTOT > SALDOACT
      * L128:                DISPLAY "Indique una cantidad menor!!"
      * L129:                       LINE 20 COLUMN 16
      * L130:                MOVE 2 TO CAMPO
      * L131:                GO TO REPEAT
      * L132:            END-IF

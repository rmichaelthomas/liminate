      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: javiertello/UnizarBank; file javiertello@UnizarBank/RETIRAREF.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L124:             ADD REINTEGRO1 TO REINTEGRO GIVING REINTEGRO.
      * L125:             DIVIDE REINTEGRO2 BY 100 GIVING CENTIMOS.
      * L126:             ADD CENTIMOS TO REINTEGRO GIVING REINTEGRO.
      * L127:             IF REINTEGRO > SALDO OR REINTEGRO = 0.00
      * L128:                 MOVE 1 TO ERROR1
      * L129:                 GO TO REPEAT
      * L130:             ELSE
      * L131:                 SUBTRACT REINTEGRO FROM SALDO GIVING SALDO
      * L132:                 REWRITE CLIENTESREC
      * L133:                 CLOSE CLIENTESFILE
      * L134:                 OPEN I-O MOVIMIENTOSFILE
      * L135:                 GO TO LEERMOV

      * Source excerpt from X-COBOL.
      * Attribution: marcel-100/gnucobol-game-of-life; file marcel-100@gnucobol-game-of-life/gol.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L177:                SET cell IN world_copy(y, x) TO 1
      * L178:              END-IF
      * L179:            ELSE
      * L180:              IF neighbours < 2 THEN
      * L181:                SET cell IN world_copy(y, x) TO 0
      * L182:              END-IF
      * L183:              IF neighbours = 2 OR neighbours = 3 THEN

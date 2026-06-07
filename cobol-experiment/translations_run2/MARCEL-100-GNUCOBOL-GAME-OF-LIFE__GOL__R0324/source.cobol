      * Source excerpt from X-COBOL.
      * Attribution: marcel-100/gnucobol-game-of-life; file marcel-100@gnucobol-game-of-life/gol.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L72:          PERFORM VARYING x FROM 1 UNTIL x > width
      * L73: 
      * L74:            MOVE FUNCTION RANDOM TO random_seed
      * L75:            COMPUTE cell_random ROUNDED = random_seed
      * L76:            SET cell IN world_real(y, x) TO cell_random
      * L77: 
      * L78:          END-PERFORM

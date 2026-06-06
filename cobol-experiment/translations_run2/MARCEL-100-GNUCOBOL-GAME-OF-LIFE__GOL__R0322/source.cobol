      * Source excerpt from X-COBOL.
      * Attribution: marcel-100/gnucobol-game-of-life; file marcel-100@gnucobol-game-of-life/gol.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L65: 
      * L66:        create_world_random SECTION.
      * L67: 
      * L68:        MOVE FUNCTION RANDOM(FUNCTION CURRENT-DATE(8:9))
      * L69:          TO random_seed
      * L70: 
      * L71:        PERFORM VARYING y FROM 1 UNTIL y > height

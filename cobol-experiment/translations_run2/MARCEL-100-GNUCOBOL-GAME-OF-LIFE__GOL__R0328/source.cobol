      * Source excerpt from X-COBOL.
      * Attribution: marcel-100/gnucobol-game-of-life; file marcel-100@gnucobol-game-of-life/gol.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L117: 
      * L118:        main_loop SECTION.
      * L119: 
      * L120:        MOVE FUNCTION CURRENT-DATE(15:1) TO random_color
      * L121: 
      * L122:        COMPUTE random_color = FUNCTION MOD(random_color, 7) + 1
      * L123: 

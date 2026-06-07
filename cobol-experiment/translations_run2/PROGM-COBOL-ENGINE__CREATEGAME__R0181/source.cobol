      * Source excerpt from X-COBOL.
      * Attribution: ProGM/COBOL-Engine; file ProGM@COBOL-Engine/CreateGame.CBL.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L30: 
      * L31:            CALL "TTF_Init".
      * L32: 
      * L33:            IF SDL-STATUS NOT = 0
      * L34:                DISPLAY "SDL_Init failed. Exiting."
      * L35:             *>    MOVE NULL-POINTER TO SDL-WINDOW
      * L36:             *>    MOVE NULL-POINTER TO SDL-RENDERER

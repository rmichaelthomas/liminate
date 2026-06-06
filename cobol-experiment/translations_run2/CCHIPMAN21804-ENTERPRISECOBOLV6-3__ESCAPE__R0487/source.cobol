      * Source excerpt from X-COBOL.
      * Attribution: cchipman21804/EnterpriseCOBOLv6.3; file cchipman21804@EnterpriseCOBOLv6.3/ESCAPE.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L371:            display "Would you like to play again? (Y/N): "
      * L372:                     with no advancing
      * L373:            accept player-in
      * L374:            move function lower-case(player-in) to player-in
      * L375:            EVALUATE true
      * L376:            when player-in is equal to "y"
      * L377:               go to 210-initialization-paragraph

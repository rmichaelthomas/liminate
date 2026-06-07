      * Source excerpt from X-COBOL.
      * Attribution: deniseyu/learning-cobol; file deniseyu@learning-cobol/rock-paper-scissors.cob.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L27:            DISPLAY 'Pick "rock", "paper", or "scissors"'.
      * L28:            ACCEPT PLAYER-CHOICE.
      * L29: 
      * L30:            COMPUTE RAND-NUM = FUNCTION RANDOM (T-MS) * 100.
      * L31:            DIVIDE RAND-NUM BY 3 GIVING BLAH REMAINDER CHOICE-IND.
      * L32:            MOVE CHOICE(CHOICE-IND + 1) TO COMPUTER-CHOICE.
      * L33:            DISPLAY 'Computer chose ' COMPUTER-CHOICE.

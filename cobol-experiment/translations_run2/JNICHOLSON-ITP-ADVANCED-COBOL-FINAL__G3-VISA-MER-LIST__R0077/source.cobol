      * Source excerpt from X-COBOL.
      * Attribution: jnicholson/ITP-Advanced-COBOL-FINAL; file jnicholson@ITP-Advanced-COBOL-FINAL/G3-VISA-MER-LIST.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L58:       ******************************************************************
      * L59:        100-DISPLAY.
      * L60:            ADD 1 TO VISA-M-CTR.
      * L61:        IF VISA-M-CTR GREATER THAN 15
      * L62:            PERFORM 300-LIST-NAVI UNTIL VISA-MER-RESP = 'N' OR 'n' OR
      * L63:                                                       'X' OR 'x'
      * L64:            DISPLAY BLANK-SCREEN

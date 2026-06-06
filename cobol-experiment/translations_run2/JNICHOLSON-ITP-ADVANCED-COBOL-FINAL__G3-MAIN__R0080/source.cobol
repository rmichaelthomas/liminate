      * Source excerpt from X-COBOL.
      * Attribution: jnicholson/ITP-Advanced-COBOL-FINAL; file jnicholson@ITP-Advanced-COBOL-FINAL/G3-MAIN.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L40:            PERFORM UNTIL WS-SEL = 'X' OR 'x'
      * L41:                DISPLAY MENUSCREEN
      * L42:                ACCEPT  MENUSCREEN
      * L43:                EVALUATE WS-SEL
      * L44:                    WHEN '1' CALL 'G3-VISA-MAIN'
      * L45:                    WHEN '2' CALL 'G3-CAP1-MAIN'
      * L46:                    WHEN '3' CALL 'G3-VFX-MAIN'

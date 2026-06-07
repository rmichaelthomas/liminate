      * Source excerpt from X-COBOL.
      * Attribution: nibrobb/1brc-cobol; file nibrobb@1brc-cobol/1brc.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L205: 
      * L206:        PRODUCE-OUTPUT.
      * L207:            DISPLAY "{" WITH NO ADVANCING.
      * L208:            COMPUTE WS-IDX = TBL-SIZE - WS-UNIQ-COUNT + 1.
      * L209:            PERFORM VARYING WS-IDX
      * L210:               FROM WS-IDX BY 1 UNTIL WS-IDX > TBL-SIZE
      * L211:                    MOVE FUNCTION TRIM(WS-MEAS-LOC(WS-IDX)) TO DSPL-LOC

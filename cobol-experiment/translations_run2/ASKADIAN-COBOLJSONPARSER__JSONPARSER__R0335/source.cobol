      * Source excerpt from X-COBOL.
      * Attribution: askadian/CobolJsonParser; file askadian@CobolJsonParser/JSONParser.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L152:             TO TRUE.
      * L153:            PERFORM UNTIL WS-JSON-IDX >= WS-JSON-MAX
      * L154:              ADD +1 TO WS-JSON-IDX
      * L155:              MOVE WS-GARBAGE(WS-JSON-IDX:1)
      * L156:                TO WS-JSON-CHAR(WS-JSON-IDX)
      * L157:              EVALUATE WS-JSON-CHAR(WS-JSON-IDX)
      * L158:                 WHEN WS-OPENING-BRACES

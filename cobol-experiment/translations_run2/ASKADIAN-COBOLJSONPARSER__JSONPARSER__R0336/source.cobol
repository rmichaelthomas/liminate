      * Source excerpt from X-COBOL.
      * Attribution: askadian/CobolJsonParser; file askadian@CobolJsonParser/JSONParser.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L281:                  MOVE WS-JSON-CHAR(WS-JSON-IDX)
      * L282:                    TO WS-TEMP-CHAR
      * L283:                  IF JSON-VAL-TYPE-UNKNOWN(WS-JSON-IDX2) THEN
      * L284:                      IF WS-TEMP-NUM IS NUMERIC THEN
      * L285:                         SET JSON-VAL-TYPE-NUMERIC(WS-JSON-IDX2) TO TRUE
      * L286:                      ELSE
      * L287:                         SET JSON-VAL-TYPE-STRING(WS-JSON-IDX2) TO TRUE

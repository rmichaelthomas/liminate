      * Source excerpt from X-COBOL.
      * Attribution: askadian/CobolJsonParser; file askadian@CobolJsonParser/JSONParser.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L133:            MOVE JSONRec TO WS-JSON-INPUT.
      * L134:       *    INITIALIZE WS-JSON.
      * L135:            MOVE 1 TO WS-JSON-INPUT-LEN.
      * L136:            UNSTRING WS-JSON-INPUT(1:10000)
      * L137:               DELIMITED BY ';;'
      * L138:               INTO WS-GARBAGE
      * L139:               WITH POINTER WS-JSON-INPUT-LEN

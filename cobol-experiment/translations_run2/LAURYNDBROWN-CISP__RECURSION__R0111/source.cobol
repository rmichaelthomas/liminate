      * Source excerpt from X-COBOL.
      * Attribution: lauryndbrown/Cisp; file lauryndbrown@Cisp/recursion.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L94:            GOBACK.
      * L95:        LOG-INIT-CALL-STACK.
      * L96:            MOVE "ADD" TO WS-LOG-OPERATION-FLAG.
      * L97:            MOVE "RECURSION:INIT" TO WS-LOG-RECORD-FUNCTION-NAME.
      * L98:            MOVE "Initialized Call Stack" TO WS-LOG-RECORD-MESSAGE.
      * L99:            CALL 'LOGGER' USING WS-LOG-OPERATION-FLAG, WS-LOG-RECORD.
      * L100:        LOG-ADD-TO-CALL-STACK.

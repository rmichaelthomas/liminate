      * Source excerpt from X-COBOL.
      * Attribution: BluAge/ServerlessCOBOLforAWS; file BluAge@ServerlessCOBOLforAWS/SQSSAMPLE.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L76:       * CHECK GETENVOP OUTCOME
      * L77: 
      * L78:        check-ge-res.
      * L79:          IF ge-op-result >= 19 THEN
      * L80:             MOVE ge-op-result TO ge-op-result-as-str
      * L81:             DISPLAY ge-op-res-displ
      * L82:             CALL "FORCEABEND" using ge-op-err-msg

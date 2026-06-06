      * Source excerpt from X-COBOL.
      * Attribution: jeroenbrons/decbox-SPK; file jeroenbrons@decbox-SPK/test.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L425: 		DISPLAY "Sucessful completion"
      * L426: 		GO TO TYPE-FILE-STATUS-EXIT.
      * L427: 
      * L428: 	IF FILE-STATUS-1 = 23
      * L429: 		DISPLAY "Invalid key, record not found"
      * L430: 		GO TO TYPE-FILE-STATUS-EXIT.
      * L431: 

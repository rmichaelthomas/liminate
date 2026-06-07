      * Source excerpt from X-COBOL.
      * Attribution: jeroenbrons/decbox-SPK; file jeroenbrons@decbox-SPK/test.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L146: **************************************************************
      * L147: 
      * L148: 	OPEN I-O RMS-INDEX-FILE.
      * L149: 	IF IGNORE-FLAG NOT = 0
      * L150: 		DISPLAY "[File not found-- creating empty file]"
      * L151: 		OPEN OUTPUT RMS-INDEX-FILE
      * L152: 		CLOSE RMS-INDEX-FILE

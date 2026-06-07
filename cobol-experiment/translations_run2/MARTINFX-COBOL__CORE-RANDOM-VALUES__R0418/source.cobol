      * Source excerpt from X-COBOL.
      * Attribution: Martinfx/Cobol; file Martinfx@Cobol/core_random_values.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L91:             RESULT = FUNCTION MOD((FRAME-COUNTER / 120), 2)
      * L92:           END-COMPUTE
      * L93: 
      * L94:           IF RESULT = 1
      * L95:             CALL "GetRandomValue" USING
      * L96:             BY VALUE -8
      * L97:             BY VALUE 5

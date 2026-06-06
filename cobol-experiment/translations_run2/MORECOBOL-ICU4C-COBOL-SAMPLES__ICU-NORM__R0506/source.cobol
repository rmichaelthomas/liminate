      * Source excerpt from X-COBOL.
      * Attribution: morecobol/icu4c-cobol-samples; file morecobol@icu4c-cobol-samples/icu-Norm.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L604:              Read  Input-File  into           Input-Buffer
      * L605:                  at End        Move 0      to Input-Read-Flag.
      * L606:            IF Input-Read-Flag = 1  Then
      * L607:              Compute Text-Length = Function Length (Input-Buffer)
      * L608:              Move    "Input Record  --------------:" to Debug-Text
      * L609:              Perform Debug-Display-sec
      * L610:              Move    Input-Buffer          to Debug-Buffer

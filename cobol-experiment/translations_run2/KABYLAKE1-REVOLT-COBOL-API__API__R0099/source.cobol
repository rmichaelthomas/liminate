      * Source excerpt from X-COBOL.
      * Attribution: kabylake1/revolt-cobol-api; file kabylake1@revolt-cobol-api/api.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L74:       *Initialize libCurl
      * L75:            call "curl-global-init" using by value x'ff' end-call.
      * L76:            call "curl-easy-init" using by reference ls-curl end-call.
      * L77:            if ls-curl is equal to null then
      * L78:                display "[API] Unable to initialize curl" end-display
      * L79:                goback
      * L80:            end-if.

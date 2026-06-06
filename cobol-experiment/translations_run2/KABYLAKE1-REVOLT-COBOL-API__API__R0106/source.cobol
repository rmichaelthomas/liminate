      * Source excerpt from X-COBOL.
      * Attribution: kabylake1/revolt-cobol-api; file kabylake1@revolt-cobol-api/api.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L354:                by value ls-chunks end-call.
      * L355:       *    call "curl-dump-slist" using
      * L356:       *        by value ls-chunks end-call.
      * L357:            evaluate ls-reqtype(1:1)
      * L358:                when 'G'
      * L359:                   call "curl-easy-setopt" using by value ls-curl
      * L360:                       by value ws-curlopt-post

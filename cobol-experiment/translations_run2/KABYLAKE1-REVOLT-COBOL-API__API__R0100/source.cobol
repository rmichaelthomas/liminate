      * Source excerpt from X-COBOL.
      * Attribution: kabylake1/revolt-cobol-api; file kabylake1@revolt-cobol-api/api.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L90:            inspect ws-text tallying ws-count
      * L91:                for characters before space.
      * L92:            add 1 to ws-count giving ws-count end-add.
      * L93:            move low-value to ws-text(ws-count:1).
      * L94:            call "curl-slist-append" using by value ls-chunks
      * L95:                by reference ws-text
      * L96:                by reference ls-chunks end-call.

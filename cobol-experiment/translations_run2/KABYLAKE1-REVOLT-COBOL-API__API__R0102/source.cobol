      * Source excerpt from X-COBOL.
      * Attribution: kabylake1/revolt-cobol-api; file kabylake1@revolt-cobol-api/api.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L136:            call "lws-create-context" using
      * L137:                by reference ws-info
      * L138:                by reference ls-ws-ctx in ls-config end-call.
      * L139:            if ls-ws-ctx is equal to null then
      * L140:                display "[API] Unable to start WebSockets" end-display
      * L141:                set return-code to 1
      * L142:                goback

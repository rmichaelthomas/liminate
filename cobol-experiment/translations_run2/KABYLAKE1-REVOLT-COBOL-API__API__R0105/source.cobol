      * Source excerpt from X-COBOL.
      * Attribution: kabylake1/revolt-cobol-api; file kabylake1@revolt-cobol-api/api.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L336:                goback
      * L337:            end-if.
      * L338:            add 1 to ws-count giving ws-count end-add.
      * L339:            move low-value to ls-endpoint(ws-count:1).
      * L340:       *    call static "cob_verify_c_str" using by reference ls-endpoint
      * L341:       *        by value function length(ls-endpoint) end-call.
      * L342:            display "[API] " ls-endpoint end-display.

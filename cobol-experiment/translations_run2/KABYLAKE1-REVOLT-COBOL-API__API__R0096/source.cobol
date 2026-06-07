      * Source excerpt from X-COBOL.
      * Attribution: kabylake1/revolt-cobol-api; file kabylake1@revolt-cobol-api/api.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L36:            end-if.
      * L37:            set ls-root in ls-config to address of ls-config.
      * L38:       *Read token from token file (if needed)
      * L39:            if ls-token(1:1) is equal to space then
      * L40:                open input sharing with all fd-token
      * L41:                read fd-token into ls-token in ls-config end-read
      * L42:                close fd-token

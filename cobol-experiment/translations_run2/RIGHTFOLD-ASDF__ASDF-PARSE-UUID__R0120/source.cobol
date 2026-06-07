      * Source excerpt from X-COBOL.
      * Attribution: rightfold/asdf; file rightfold@asdf/asdf-parse-uuid.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L56:            .
      * L57: 
      * L58:        para-nibble.
      * L59:            COMPUTE ws-nibble = FUNCTION ORD(ls-in(ws-j : 1)) - 1
      * L60:            EVALUATE ws-nibble
      * L61:            WHEN ws-ord-0 THRU ws-ord-9
      * L62:                SUBTRACT ws-ord-0 FROM ws-nibble

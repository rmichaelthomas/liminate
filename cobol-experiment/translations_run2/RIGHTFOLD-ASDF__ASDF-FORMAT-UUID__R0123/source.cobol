      * Source excerpt from X-COBOL.
      * Attribution: rightfold/asdf; file rightfold@asdf/asdf-format-uuid.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L56:            WHEN  0 THRU  9
      * L57:                ADD ws-ord-0 TO ws-nibble
      * L58:            WHEN 10 THRU 15
      * L59:                COMPUTE ws-nibble = ws-nibble - 10 + ws-ord-a
      * L60:            END-EVALUATE
      * L61:            MOVE FUNCTION CHAR(ws-nibble + 1) TO ls-out(ws-j : 1)
      * L62:            .

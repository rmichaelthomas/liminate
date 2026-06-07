      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: fgregg/tax_extension; file fgregg@tax_extension/ASHMA839.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L1083: 01083              SUBTRACT WS-PRIOR-MINIMUM FROM PREV-BASE
      * L1084: 01084              IF PREV-ADJ-BASE < 0
      * L1085: 01085                 MOVE ZEROS TO PREV-ADJ-BASE
      * L1086: 01086              END-IF
      * L1087: 01087              COMPUTE PREV-ADJ-BASE ROUNDED =
      * L1088: 01088                  PREV-BASE * PREV-MULTIPLY
      * L1089: 01089              IF PREV-ADJ-BASE < 0
      * L1090: 01090                 MOVE ZEROS TO PREV-ADJ-BASE
      * L1091: 01091              END-IF

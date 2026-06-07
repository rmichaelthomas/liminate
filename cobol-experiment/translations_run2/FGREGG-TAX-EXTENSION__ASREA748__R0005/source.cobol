      * Source excerpt from X-COBOL.
      * Attribution: fgregg/tax_extension; file fgregg@tax_extension/ASREA748.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L204: 00204          MOVE 1ST-TIME-VAL TO FA-FRST-TIME
      * L205: 00205          MOVE EXP-INC-VAL  TO FA-EXPINC
      * L206: 00206          MOVE TOT-ASSD-VAL TO FA-TOT-FROZ
      * L207: 00207          COMPUTE FA-FROZ-EQLZD ROUNDED =
      * L208: 00208                 TOT-ASSD-VAL * LINK-EQFCTR-N
      * L209: 00209          COMPUTE FA-FROZ-TXAMT ROUNDED =
      * L210: 00210                (FA-TOT-FROZ * TXCD-TXCDE-RATE) / 100

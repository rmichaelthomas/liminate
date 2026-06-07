      * Source excerpt from X-COBOL.
      * Attribution: fgregg/tax_extension; file fgregg@tax_extension/ASREA748.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L206: 00206          MOVE TOT-ASSD-VAL TO FA-TOT-FROZ
      * L207: 00207          COMPUTE FA-FROZ-EQLZD ROUNDED =
      * L208: 00208                 TOT-ASSD-VAL * LINK-EQFCTR-N
      * L209: 00209          COMPUTE FA-FROZ-TXAMT ROUNDED =
      * L210: 00210                (FA-TOT-FROZ * TXCD-TXCDE-RATE) / 100
      * L211: 00211          COMPUTE FA-EXPINCEV ROUNDED =
      * L212: 00212                 EXP-INC-VAL * LINK-EQFCTR-N

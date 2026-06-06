      * Source excerpt from X-COBOL.
      * Attribution: fgregg/tax_extension; file fgregg@tax_extension/ASREA748.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L210: 00210                (FA-TOT-FROZ * TXCD-TXCDE-RATE) / 100
      * L211: 00211          COMPUTE FA-EXPINCEV ROUNDED =
      * L212: 00212                 EXP-INC-VAL * LINK-EQFCTR-N
      * L213: 00213          COMPUTE FA-EXPINCTX ROUNDED =
      * L214: 00214                (FA-EXPINCEV * TXCD-TXCDE-RATE) / 100
      * L215: 00215          WRITE FRZAGCY-REC
      * L216: 00216          ADD +1 TO RECS-OUT-CNTR.

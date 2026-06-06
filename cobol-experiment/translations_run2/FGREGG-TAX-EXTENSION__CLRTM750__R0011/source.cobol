      * Source excerpt from X-COBOL.
      * Attribution: fgregg/tax_extension; file fgregg@tax_extension/CLRTM750.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L241: 00241      OPEN INPUT FRZAGCY-FILE
      * L242: 00242          OUTPUT PRINT-FILE APPEND-FILE.
      * L243: 00243      SKIP1
      * L244: 00244      MOVE FUNCTION CURRENT-DATE(1:8) TO ACPT-DATE.
      * L245: 00245      STRING ACPT-DATE(5:2) '/' ACPT-DATE(7:2) '/' ACPT-DATE(3:2)
      * L246: 00246             DELIMITED BY SIZE INTO HD2-DATE.
      * L247: 00247      MOVE LINK-EQFCTR-N TO HD2-FACT.

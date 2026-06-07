      * Source excerpt from X-COBOL.
      * Attribution: fgregg/tax_extension; file fgregg@tax_extension/ASREA748.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L122: 00122          DISPLAY 'INVALID CLOSE ON TXCD MSTR FILE'
      * L123: 00123          DISPLAY 'FILE STATUS IS ' FILE-STATUS
      * L124: 00124          DISPLAY 'FEEDBACK STATUS IS ' FS-RETURN ' '
      * L125: 00125                    FS-FUNCTION ' ' FS-FEEDBACK
      * L126: 00126          MOVE 16 TO RETURN-CODE.
      * L127: 00127      SKIP1
      * L128: 00128      CLOSE FRZDIV-PRCNT-FILE  FRZAGCY-FILE.

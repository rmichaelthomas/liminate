      * Source excerpt from X-COBOL.
      * Attribution: JohnDovey/GNUCobol-Samples; file JohnDovey@GNUCobol-Samples/GCic.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L754:        200-Let-User-Set-Switches SECTION.
      * L755:            SET WS-RS-Switch-Changes-BOOL TO TRUE
      * L756:            PERFORM UNTIL WS-RS-No-Switch-Changes-BOOL
      * L757: GC1213         EVALUATE WS-Listing-CD
      * L758: GC1213         WHEN 0
      * L759: GC1213             MOVE 'Listing Off'            TO WS-Listing-TXT
      * L760: GC1213             MOVE SPACE                    TO WS-CS-LISTING-CHR

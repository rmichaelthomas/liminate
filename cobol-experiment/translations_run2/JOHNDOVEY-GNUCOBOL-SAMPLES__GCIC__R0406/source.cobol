      * Source excerpt from X-COBOL.
      * Attribution: JohnDovey/GNUCobol-Samples; file JohnDovey@GNUCobol-Samples/GCic.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L764: GC1213         WHEN 2
      * L765: GC1213             MOVE 'Listing On (Portrait)' TO WS-Listing-TXT
      * L766: GC1213             MOVE SELCHAR                  TO WS-CS-LISTING-CHR
      * L767: GC1213         END-EVALUATE
      * L768:                ACCEPT S-Switches-SCR
      * L769:                IF COB-CRT-STATUS > 0
      * L770:                    EVALUATE COB-CRT-STATUS

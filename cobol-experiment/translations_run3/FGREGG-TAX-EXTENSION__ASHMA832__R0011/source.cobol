      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: fgregg/tax_extension; file fgregg@tax_extension/ASHMA832.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L383: 00383            MOVE PR-KEYPCL  TO CUR-KEYPCL
      * L384: 00384            MOVE PR-PROP  TO CUR-PROP
      * L385: 00385            MOVE PR-RECCD  TO CUR-RECCD
      * L386: 00386            IF CUR-REC-KEY >= PREV-REC-KEY
      * L387: 00387               MOVE CUR-REC-KEY  TO PREV-REC-KEY
      * L388: 00388            ELSE
      * L389: 00389               MOVE 16  TO RETURN-CODE
      * L390: 00390               SET SEVERE-ERROR  TO TRUE
      * L391: 00391               MOVE REC-READ-CTR  TO CTR-DISPLAY
      * L392: 00392               DISPLAY SPACES

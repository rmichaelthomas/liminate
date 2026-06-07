      * Source excerpt from X-COBOL.
      * Attribution: RegiBrazil/health-pipeline; file RegiBrazil@health-pipeline/HCM1PL01.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L119:                 TO HCM1DFR1O
      * L120:            END-IF
      * L121: 
      * L122:            IF CA-NUM-MEDICATIONS > 1
      * L123:               MOVE CA-DRUG-NAME OF CA-MEDICATIONS (2)
      * L124:                 TO HCM1DNA2O
      * L125:               MOVE CA-STRENGTH OF CA-MEDICATIONS (2)

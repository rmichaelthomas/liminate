      * Source excerpt from X-COBOL.
      * Attribution: RegiBrazil/health-pipeline; file RegiBrazil@health-pipeline/HCM1PL01.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L106:                      LENGTH(LENGTH OF COMM-AREA)
      * L107:            END-EXEC
      * L108: 
      * L109:            IF CA-NUM-MEDICATIONS > 0
      * L110:               MOVE CA-DRUG-NAME OF CA-MEDICATIONS (1)
      * L111:                 TO HCM1DNA1O
      * L112:               MOVE CA-STRENGTH OF CA-MEDICATIONS (1)

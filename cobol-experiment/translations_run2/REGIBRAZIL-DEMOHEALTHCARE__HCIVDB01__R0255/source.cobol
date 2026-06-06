      * Source excerpt from X-COBOL.
      * Attribution: RegiBrazil/DemoHealthCare; file RegiBrazil@DemoHealthCare/HCIVDB01.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L139:            MOVE CA-VISIT-DATE   TO DB2-TIMESTAMP(1:10)
      * L140:            MOVE SPACE           TO DB2-TIMESTAMP (11:1)
      * L141:            IF CA-VISIT-TIME(10:) EQUAL SPACE
      * L142:               MOVE '.0' TO CA-VISIT-TIME(9:2)
      * L143:            END-IF
      * L144:            MOVE CA-VISIT-TIME   TO DB2-TIMESTAMP(12:10)
      * L145:            MOVE '00000'         TO DB2-TIMESTAMP(22:5)

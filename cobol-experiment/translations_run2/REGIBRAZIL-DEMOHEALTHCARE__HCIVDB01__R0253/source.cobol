      * Source excerpt from X-COBOL.
      * Attribution: RegiBrazil/DemoHealthCare; file RegiBrazil@DemoHealthCare/HCIVDB01.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L136:       * and save in error msg field incase required
      * L137:            MOVE CA-PATIENT-ID TO EM-PATNUM
      * L138:       * format date and time into timestamp
      * L139:            MOVE CA-VISIT-DATE   TO DB2-TIMESTAMP(1:10)
      * L140:            MOVE SPACE           TO DB2-TIMESTAMP (11:1)
      * L141:            IF CA-VISIT-TIME(10:) EQUAL SPACE
      * L142:               MOVE '.0' TO CA-VISIT-TIME(9:2)

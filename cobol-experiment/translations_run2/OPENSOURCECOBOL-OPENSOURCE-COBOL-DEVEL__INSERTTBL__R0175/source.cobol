      * Source excerpt from X-COBOL.
      * Attribution: opensourcecobol/opensource-cobol-devel; file opensourcecobol@opensource-cobol-devel/INSERTTBL.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L103:                  INSERT INTO EMP VALUES
      * L104:                         (:EMP-NO,:EMP-NAME,:EMP-SALARY)
      * L105:               END-EXEC
      * L106:               IF  SQLCODE NOT = ZERO
      * L107:                   PERFORM ERROR-RTN
      * L108:                   EXIT PERFORM
      * L109:               END-IF

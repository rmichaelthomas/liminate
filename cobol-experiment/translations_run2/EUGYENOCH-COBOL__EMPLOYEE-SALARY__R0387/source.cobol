      * Source excerpt from X-COBOL.
      * Attribution: eugyenoch/cobol; file eugyenoch@cobol/employee-salary.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L120: IF CONT = 0 THEN
      * L121: CALL âCBL_CHECK_FILE EXISTâ USING âTRAN1.DATâ
      * L122: RETURNING T-FILE
      * L123: IF T-FILE = O THEN
      * L124: PERFORM REPORT-PARA
      * L125: ELSE
      * L126: PERFORM CONVERT-PARA

      * Source excerpt from X-COBOL.
      * Attribution: opensourcecobol/opensource-cobol-devel; file opensourcecobol@opensource-cobol-devel/INSERTTBL.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L63:            EXEC SQL
      * L64:                CONNECT :USERNAME IDENTIFIED BY :PASSWD USING :DBNAME
      * L65:            END-EXEC.
      * L66:            IF  SQLCODE NOT = ZERO PERFORM ERROR-RTN STOP RUN.
      * L67: 
      * L68:       *    DROP TABLE
      * L69:            EXEC SQL

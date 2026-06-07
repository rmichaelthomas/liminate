      * Source excerpt from X-COBOL.
      * Attribution: RegiBrazil/health-pipeline; file RegiBrazil@health-pipeline/HCMAPL01.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L74:                      INTO(HCMAMAPI) ASIS TERMINAL
      * L75:                      MAPSET('HCMAPS') END-EXEC.
      * L76: 
      * L77:            IF HCMADNAMO EQUAL ZEROS OR SPACES OR LOW-VALUES
      * L78:               PERFORM GET-PATIENT
      * L79:               Move 'Enter medication information'
      * L80:                   To  HCMAMSGO

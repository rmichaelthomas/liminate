      * Source excerpt from X-COBOL.
      * Attribution: zosconnect/zosconnect-sample-cobol-apirequester; file zosconnect@zosconnect-sample-cobol-apirequester/imsclaim.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L305:       *
      * L306:            CALL 'CBLTDLI' USING DLI-GET-UNIQUE IO-PCB-MASK
      * L307:                                 INPUT-MSG
      * L308:            IF IO-PCB-STATUS-CODE NOT = SPACES AND
      * L309:               IO-PCB-STATUS-CODE NOT = DLI-END-MESSAGES
      * L310:              DISPLAY 'GU FAILED WITH IO-PCB-STATUS-CODE('
      * L311:                      IO-PCB-STATUS-CODE ')'

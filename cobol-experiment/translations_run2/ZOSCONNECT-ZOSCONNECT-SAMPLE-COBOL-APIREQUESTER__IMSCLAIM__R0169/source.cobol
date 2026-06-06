      * Source excerpt from X-COBOL.
      * Attribution: zosconnect/zosconnect-sample-cobol-apirequester; file zosconnect@zosconnect-sample-cobol-apirequester/imsclaim.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L318:       *
      * L319:            CALL 'CBLTDLI' USING DLI-INSERT IO-PCB-MASK
      * L320:                                 OUTPUT-MSG
      * L321:            IF IO-PCB-STATUS-CODE NOT = SPACES
      * L322:              DISPLAY 'ISRT FAILED WITH IO-PCB-STATUS-CODE('
      * L323:                      IO-PCB-STATUS-CODE ')'
      * L324:            END-IF

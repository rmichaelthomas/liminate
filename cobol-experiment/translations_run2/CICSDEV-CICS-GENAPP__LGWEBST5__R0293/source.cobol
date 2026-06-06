      * Source excerpt from X-COBOL.
      * Attribution: cicsdev/cics-genapp; file cicsdev@cics-genapp/lgwebst5.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L791:                      Length(Length of WS-TSQdata)
      * L792:                      Resp(WS-RESP)
      * L793:            End-Exec.
      * L794:            Compute DRateVal = NRateVal - ORateVal
      * L795:            Move DRateVal   To WS-TSQdata
      * L796:            Exec Cics WRITEQ TS Queue(WS-TSQname)
      * L797:                      FROM(WS-TSQdata)

      * Source excerpt from X-COBOL.
      * Attribution: cicsdev/cics-genapp; file cicsdev@cics-genapp/lgwebst5.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L723:                      Length(Length of WS-OLDV)
      * L724:                      Resp(WS-RESP)
      * L725:            End-Exec.
      * L726:            If WS-RESP Not = DFHRESP(NORMAL)
      * L727:             Move '120000' To WS-OLDV.
      * L728: 
      * L729:            Exec Cics DeleteQ TS Queue(WS-TSQNAME)

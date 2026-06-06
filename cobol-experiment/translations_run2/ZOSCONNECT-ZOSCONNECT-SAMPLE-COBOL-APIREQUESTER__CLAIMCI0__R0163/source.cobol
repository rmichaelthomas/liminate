      * Source excerpt from X-COBOL.
      * Attribution: zosconnect/zosconnect-sample-cobol-apirequester; file zosconnect@zosconnect-sample-cobol-apirequester/claimci0.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L155:                     PERFORM DO-WRITE-TO-CSMT
      * L156:                     PERFORM DO-RETURN-TO-CICS
      * L157:                 WHEN DFHRESP(CCSIDERR)
      * L158:                     IF RSP-CLAIM-CICS-RESP = 3
      * L159:                          STRING 'CONTAINER '
      * L160:                           DELIMITED BY SIZE
      * L161:                           WS-CONTAINER-NAME

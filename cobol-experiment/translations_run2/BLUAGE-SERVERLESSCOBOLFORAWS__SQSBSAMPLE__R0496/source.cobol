      * Source excerpt from X-COBOL.
      * Attribution: BluAge/ServerlessCOBOLforAWS; file BluAge@ServerlessCOBOLforAWS/SQSBSAMPLE.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L94:       * PULL ATOMIC MESSAGE
      * L95:        CALL "SQSOP" using sqs-request-area msg-body sqs-op-result
      * L96:        PERFORM Checksqs-op-result
      * L97:        IF sqs-op-result NOT EQUAL 4
      * L98:          ADD 1 TO msg-pul-cnt
      * L99:       * DISPLAY MSG
      * L100:          DISPLAY "Pulled Message content " msg-body

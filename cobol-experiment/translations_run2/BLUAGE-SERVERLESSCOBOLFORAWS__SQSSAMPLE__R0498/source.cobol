      * Source excerpt from X-COBOL.
      * Attribution: BluAge/ServerlessCOBOLforAWS; file BluAge@ServerlessCOBOLforAWS/SQSSAMPLE.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L54:         send-to-out.
      * L55:            SET clear-text TO TRUE
      * L56:            STRING msg-body-header DELIMITED BY ':'
      * L57:                  msg-body-data(1:msg-body-len)
      * L58:                  DELIMITED BY '#' INTO msg-body-fwd
      * L59:            SET sqs-send-single-message TO TRUE
      * L60:            CALL "SQSOP" using sqs-request-area

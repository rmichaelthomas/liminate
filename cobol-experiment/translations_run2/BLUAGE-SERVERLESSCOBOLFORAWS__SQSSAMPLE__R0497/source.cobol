      * Source excerpt from X-COBOL.
      * Attribution: BluAge/ServerlessCOBOLforAWS; file BluAge@ServerlessCOBOLforAWS/SQSSAMPLE.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L40:        procedure division using msg-body.
      * L41: 
      * L42:        Main.
      * L43:            DISPLAY "Triggering message:" msg-body-data(1:msg-body-len)
      * L44:            PERFORM get-config-from-env
      * L45: 
      * L46:       *  SEND BACK TO ANOTHER QUEUE

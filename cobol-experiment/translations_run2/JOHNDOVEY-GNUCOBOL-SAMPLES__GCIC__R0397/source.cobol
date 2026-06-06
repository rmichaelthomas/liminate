      * Source excerpt from X-COBOL.
      * Attribution: JohnDovey/GNUCobol-Samples; file JohnDovey@GNUCobol-Samples/GCic.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L601:                REPLACING STATUS BY WS-FSM-Status-CD
      * L602:                          MSG    BY WS-FSM-Msg-TXT.
      * L603:            MOVE SPACES TO WS-Output-Msg-TXT
      * L604:            IF WS-FSM-Status-CD = 35
      * L605:                DISPLAY
      * L606:                    'File not found: "'
      * L607:                    TRIM(WS-File-Name-TXT,TRAILING)

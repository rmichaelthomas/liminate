      * Source excerpt from X-COBOL.
      * Attribution: JohnDovey/GNUCobol-Samples; file JohnDovey@GNUCobol-Samples/GCic.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L664:       *>***************************************************************
      * L665: GC0712     ACCEPT WS-Cmd-Args-TXT FROM COMMAND-LINE
      * L666: GC0712     MOVE 1 TO WS-Cmd-SUB
      * L667: GC0712     IF WS-Cmd-Args-TXT(WS-Cmd-SUB:1) = '"' OR "'"
      * L668: GC0712         MOVE WS-Cmd-Args-TXT(WS-Cmd-SUB:1)
      * L669: GC0712           TO WS-Cmd-End-Quote-CHR
      * L670: GC0712         ADD 1 TO WS-Cmd-SUB

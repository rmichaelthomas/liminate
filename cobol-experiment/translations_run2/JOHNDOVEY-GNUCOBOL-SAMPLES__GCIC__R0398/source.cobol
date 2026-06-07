      * Source excerpt from X-COBOL.
      * Attribution: JohnDovey/GNUCobol-Samples; file JohnDovey@GNUCobol-Samples/GCic.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L648:       *>***************************************************************
      * L649:       *> Get GCic Compilation Date/Time                              **
      * L650:       *>***************************************************************
      * L651:            MOVE WHEN-COMPILED (1:12) TO WS-OC-Compile-DT
      * L652:            INSPECT WS-OC-Compile-DT
      * L653:                REPLACING ALL '/' BY ':'
      * L654:                AFTER INITIAL SPACE

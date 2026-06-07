      * Source excerpt from X-COBOL.
      * Attribution: JohnDovey/GNUCobol-Samples; file JohnDovey@GNUCobol-Samples/GCic.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L709:                         WS-Prog-File-Name-TXT
      * L710: GC0712         MOVE WS-OS-Dir-CHR TO WS-FN-CHR (WS-I-SUB)
      * L711:            END-IF
      * L712:            IF WS-Prog-Folder-TXT = SPACES
      * L713:                ACCEPT WS-Prog-Folder-TXT FROM ENVIRONMENT 'CD'
      * L714: GC0909     ELSE
      * L715: GC0909         CALL 'CBL_CHANGE_DIR'

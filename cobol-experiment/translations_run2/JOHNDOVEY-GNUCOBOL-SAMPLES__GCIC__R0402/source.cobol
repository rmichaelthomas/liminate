      * Source excerpt from X-COBOL.
      * Attribution: JohnDovey/GNUCobol-Samples; file JohnDovey@GNUCobol-Samples/GCic.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L691:       *> Split 'WS-File-Name-TXT' into 'WS-Prog-Folder-TXT' and      **
      * L692:       *> 'WS-Prog-File-Name-TXT'                                     **
      * L693:       *>***************************************************************
      * L694: GC0909     IF WS-OS-Cygwin-BOOL AND WS-File-Name-TXT (2:1) = ':'
      * L695: GC0712         MOVE '\' TO WS-OS-Dir-CHR
      * L696: GC0909     END-IF
      * L697: GC0712     MOVE LENGTH(WS-File-Name-TXT) TO WS-I-SUB

      * Source excerpt from X-COBOL.
      * Attribution: Apress/cobol-VB-on-.net; file Apress@cobol-VB-on-.net/Form1.cob.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L149: 001490 01 disposing OBJECT REFERENCE CLASS-BOOLEAN.
      * L150: 001500 PROCEDURE DIVISION USING BY VALUE disposing.
      * L151: 001510     SET TEMP-1 TO disposing.
      * L152: 001520     IF TEMP-1 = B"1" THEN
      * L153: 001530       IF components NOT = NULL THEN
      * L154: 001540         INVOKE components "Dispose"
      * L155: 001550       END-IF

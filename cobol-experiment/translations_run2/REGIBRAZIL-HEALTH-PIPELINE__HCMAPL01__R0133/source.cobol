      * Source excerpt from X-COBOL.
      * Attribution: RegiBrazil/health-pipeline; file RegiBrazil@health-pipeline/HCMAPL01.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L97:                         COMMAREA(COMM-AREA)
      * L98:                         LENGTH(32500)
      * L99:               END-EXEC
      * L100:               IF CA-RETURN-CODE > 0
      * L101:                  Exec CICS Syncpoint Rollback End-Exec
      * L102:                  GO TO NO-ADD
      * L103:               END-IF

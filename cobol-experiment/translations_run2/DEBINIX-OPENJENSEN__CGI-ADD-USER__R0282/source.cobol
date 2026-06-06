      * Source excerpt from X-COBOL.
      * Attribution: debinix/openjensen; file debinix@openjensen/cgi-add-user.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L211:                                             USING :wc-database
      * L212:            END-EXEC
      * L213: 
      * L214:            IF  SQLSTATE NOT = ZERO
      * L215:                 PERFORM Z0100-error-routine
      * L216:            ELSE
      * L217:                 SET is-db-connected TO true

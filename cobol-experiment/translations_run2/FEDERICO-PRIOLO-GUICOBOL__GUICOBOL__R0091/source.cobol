      * Source excerpt from X-COBOL.
      * Attribution: federico-priolo/GuiCOBOL; file federico-priolo@GuiCOBOL/guicobol.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L253: 002530** manage the free format option
      * L254: 002540*
      * L255: 002550
      * L256: 002560          IF SW-FREE =  "S"
      * L257: 002570          AND REC-IN > SPACES
      * L258: 002580           PERFORM VARYING IND FROM 1 BY 1 UNTIL IND > 100
      * L259: 002590            OR REC-IN(IND:1) NOT = SPACES

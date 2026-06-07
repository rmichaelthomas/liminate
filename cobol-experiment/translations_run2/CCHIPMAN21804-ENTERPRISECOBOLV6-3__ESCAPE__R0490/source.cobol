      * Source excerpt from X-COBOL.
      * Attribution: cchipman21804/EnterpriseCOBOLv6.3; file cchipman21804@EnterpriseCOBOLv6.3/ESCAPE.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L500:            end-if
      * L501: 
      * L502:            if function test-numval(pursuers-in) is not equal zero then
      * L503:               display "Pursuers quantity is not numeric."
      * L504:               go to 130-pursuers-prompt
      * L505:            else
      * L506:               compute pursuers = function numval(pursuers-in)

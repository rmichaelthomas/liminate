      * Source excerpt from X-COBOL.
      * Attribution: RegiBrazil/DemoHealthCare; file RegiBrazil@DemoHealthCare/HCAPDB02.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L162:                            :CA-USERID )
      * L163:              END-EXEC
      * L164: 
      * L165:              IF SQLCODE NOT EQUAL 0
      * L166:                MOVE '90' TO CA-RETURN-CODE
      * L167:                PERFORM WRITE-ERROR-MESSAGE
      * L168:                EXEC CICS RETURN END-EXEC

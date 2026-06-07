      * Source excerpt from X-COBOL.
      * Attribution: ignamiguel/fiuba-algoritmos-4-cobol; file ignamiguel@fiuba-algoritmos-4-cobol/credit_card-sample-full.cob.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L217:             PERFORM Print_Cupon_Details
      * L218: 
      * L219:             MOVE C1-IMPORTE TO WS-C1-IMPORTE
      * L220:             COMPUTE WS-C1-IMPORTE = FUNCTION NUMVAL(WS-C1-IMPORTE)
      * L221:             END-COMPUTE
      * L222: 
      * L223:             COMPUTE WS-total-amount = (WS-total-amount + WS-C1-IMPORTE)

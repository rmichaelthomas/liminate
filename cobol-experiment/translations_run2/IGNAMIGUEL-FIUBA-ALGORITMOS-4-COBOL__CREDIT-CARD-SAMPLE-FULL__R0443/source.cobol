      * Source excerpt from X-COBOL.
      * Attribution: ignamiguel/fiuba-algoritmos-4-cobol; file ignamiguel@fiuba-algoritmos-4-cobol/credit_card-sample-full.cob.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L220:             COMPUTE WS-C1-IMPORTE = FUNCTION NUMVAL(WS-C1-IMPORTE)
      * L221:             END-COMPUTE
      * L222: 
      * L223:             COMPUTE WS-total-amount = (WS-total-amount + WS-C1-IMPORTE)
      * L224: 
      * L225:             READ Cupon1_file NEXT RECORD
      * L226:              AT END SET EOF-CUPON-1 TO TRUE

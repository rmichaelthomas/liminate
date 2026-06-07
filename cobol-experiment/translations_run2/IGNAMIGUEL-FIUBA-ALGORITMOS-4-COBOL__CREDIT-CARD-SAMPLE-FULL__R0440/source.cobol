      * Source excerpt from X-COBOL.
      * Attribution: ignamiguel/fiuba-algoritmos-4-cobol; file ignamiguel@fiuba-algoritmos-4-cobol/credit_card-sample-full.cob.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L188:        Print_Amounts.
      * L189:            DISPLAY "------------------------------------".
      * L190:            DISPLAY "Total de la tarjeta: " WS-total-amount.
      * L191:            COMPUTE WS-Saldo-amount = FUNCTION NUMVAL(WS-Saldo-amount)
      * L192:            END-COMPUTE
      * L193:            COMPUTE WS-total-amount = WS-total-amount + WS-Saldo-amount.
      * L194:            DISPLAY "Saldo final: " WS-total-amount.

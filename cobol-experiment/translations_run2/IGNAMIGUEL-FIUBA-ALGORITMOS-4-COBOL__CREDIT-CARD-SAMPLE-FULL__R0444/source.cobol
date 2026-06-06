      * Source excerpt from X-COBOL.
      * Attribution: ignamiguel/fiuba-algoritmos-4-cobol; file ignamiguel@fiuba-algoritmos-4-cobol/credit_card-sample-full.cob.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L330:           *>NOT INVALID KEY DISPLAY "Saldo Pointer Updated :- "SaldoStatus
      * L331:          END-START.
      * L332: 
      * L333:         IF SaldoStatus = "00"
      * L334:            READ SaldoFile NEXT RECORD
      * L335:               AT END SET EOF-SALDO TO TRUE
      * L336:            END-READ

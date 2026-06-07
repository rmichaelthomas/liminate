      * Source excerpt from X-COBOL.
      * Attribution: lucasrmagalhaes/learning-COBOL; file lucasrmagalhaes@learning-COBOL/PGM.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L66:                'ANO DE ENTRADA: ' WS05-ANOENTRADA(WS77-IND) ' '
      * L67:                'SALARIO: ' WS05-SALARIO(WS77-IND).
      * L68: 
      * L69:                COMPUTE WS77-TEMPOCASA = WS03-ANO -
      * L70:                WS05-ANOENTRADA(WS77-IND).
      * L71:                    EVALUATE WS77-TEMPOCASA
      * L72:                        WHEN 0 THRU 1

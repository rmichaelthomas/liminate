      * Source excerpt from X-COBOL.
      * Attribution: lucasrmagalhaes/learning-COBOL; file lucasrmagalhaes@learning-COBOL/PGM.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L70:                WS05-ANOENTRADA(WS77-IND).
      * L71:                    EVALUATE WS77-TEMPOCASA
      * L72:                        WHEN 0 THRU 1
      * L73:                    COMPUTE WS77-AUMENTO = 0
      * L74:                        WHEN 2 THRU 5
      * L75:                    COMPUTE WS77-AUMENTO =
      * L76:                    (WS05-SALARIO(WS77-IND) / 100) * 0,05

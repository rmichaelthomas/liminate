      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: RocketSoftwareCOBOLandMainframe/BankDemo; file RocketSoftwareCOBOLandMainframe@BankDemo/BBANK70P.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L238:            DIVIDE WS-LOAN-INTEREST BY 12
      * L239:              GIVING WS-LOAN-INTEREST ROUNDED.
      * L240:            COMPUTE WS-LOAN-MONTHLY-PAYMENT ROUNDED =
      * L241:              ((WS-LOAN-INTEREST * ((1 + WS-LOAN-INTEREST)
      * L242:                  ** WS-LOAN-TERM)) /
      * L243:              (((1 + WS-LOAN-INTEREST) ** WS-LOAN-TERM) - 1 ))
      * L244:                * WS-LOAN-PRINCIPAL.
      * L245:            MOVE WS-LOAN-MONTHLY-PAYMENT TO WS-CALC-WORK-PAYMENT-N.

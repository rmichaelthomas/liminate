      * Source excerpt from X-COBOL.
      * Attribution: victorqribeiro/perceptronCobol; file victorqribeiro@perceptronCobol/perceptron.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L60:                      COMPUTE PREDICTION = PREDICTION + W3 * FEAT3
      * L61:                      COMPUTE PREDICTION = PREDICTION + W4 * FEAT4
      * L62:                      COMPUTE ERR = Y - PREDICTION
      * L63:                      COMPUTE B = B + ERR * LR
      * L64:                      COMPUTE TMP = W1 * FEAT1 * ERR * LR
      * L65:                      COMPUTE W1 = W1 + TMP
      * L66:                      COMPUTE TMP = W2 * FEAT2 * ERR * LR

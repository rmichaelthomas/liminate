      * Source excerpt from X-COBOL.
      * Attribution: adrianotelesc/crud-payroll; file adrianotelesc@crud-payroll/payroll.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L308:            EVALUATE TRUE
      * L309:            WHEN ((FS-SALBR - FS-INSS) - FS-TOTAL-DEP > 1903,98) AND
      * L310:       -(((FS-SALBR - FS-INSS) - FS-TOTAL-DEP) <= 2826,65)
      * L311:                COMPUTE FS-IRRF = (((FS-SALBR - FS-INSS) - FS-TOTAL-DEP)
      * L312:       - * 0,075) - 142,80
      * L313:            WHEN (((FS-SALBR - FS-INSS) - FS-TOTAL-DEP) > 2826,65
      * L314:       -) AND (((FS-SALBR - FS-INSS) - (FS-DEP * 189,59)) <= 3751,05)

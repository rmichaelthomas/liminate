      * Source excerpt from X-COBOL (2024 release, Zenodo 14269462).
      * Attribution: adrianotelesc/crud-payroll; file adrianotelesc@crud-payroll/payroll.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L291:            EVALUATE TRUE
      * L292:            WHEN (FS-SALBR > 0) AND (FS-SALBR <= 1556,94)
      * L293:                COMPUTE FS-INSS = FS-SALBR * 0,08
      * L294:            WHEN (FS-SALBR > 1556,94) AND (FS-SALBR <= 2594,92)
      * L295:                COMPUTE FS-INSS = FS-SALBR * 0,09
      * L296:            WHEN (FS-SALBR > 2594,92) AND (FS-SALBR <= 5189,82)
      * L297:                COMPUTE FS-INSS = FS-SALBR * 0,11
      * L298:            WHEN (FS-SALBR > 5189,82)
      * L299:                COMPUTE FS-INSS = 5189,82 * 0,11
      * L300:            END-EVALUATE.

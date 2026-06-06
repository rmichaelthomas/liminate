      * Source excerpt from X-COBOL.
      * Attribution: morecobol/icu4c-cobol-samples; file morecobol@icu4c-cobol-samples/icu-Norm.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L353:            Call    "GetProcAddress" using  by value     DLL-Handle
      * L354:                                            by reference API-Name
      * L355:                                            Returning    API-Pointer.
      * L356:            IF API-Pointer = NULL
      * L357:               Move     "The following API was not found in DLL:"
      * L358:                                            to Debug-Text
      * L359:               Move     API-Name            to Debug-Value

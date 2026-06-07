      * Source excerpt from X-COBOL.
      * Attribution: morecobol/icu4c-cobol-samples; file morecobol@icu4c-cobol-samples/icu-Norm.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L320:       *
      * L321:            Call    "LoadLibraryA"  using by reference  DLL-Name
      * L322:                                    Returning           DLL-Handle.
      * L323:            IF DLL-Handle = ZEROS
      * L324:               Move     "Couldn't load "    to Debug-Text
      * L325:               Move     DLL-Name            to Debug-Value
      * L326:               Move     1                   to Error-Display-sw

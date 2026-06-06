      * Source excerpt from X-COBOL.
      * Attribution: gaessaki/COBOLCalc; file gaessaki@COBOLCalc/Window1.xaml.cbl.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L176:            01 ls-temp pic x(25) value is OutputBox::Text.
      * L177:            01 ls-number decimal value is 0.
      * L178:        procedure division using by value sender as object e as type System.Windows.RoutedEventArgs.
      * L179:            set ls-number = function numval(ls-temp)
      * L180:            set ls-number to ls-number * -1
      * L181:            set OutputBox::Text to ls-number
      * L182:        end method.

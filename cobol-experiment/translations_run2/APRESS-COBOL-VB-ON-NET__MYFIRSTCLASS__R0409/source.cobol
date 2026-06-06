      * Source excerpt from X-COBOL.
      * Attribution: Apress/cobol-VB-on-.net; file Apress@cobol-VB-on-.net/MyFirstClass.cob.
      * License: Zenodo X-COBOL dataset, CC-BY-4.0.
      * Excerpt only; not the complete upstream file.
      * L42: 000231     RAISING CLASS-ARGUMENTEXCEPTION.
      * L43: 000240*    The Input Parm is tested to be non-blank for DEMO purposes
      * L44: 000241     SET MyString TO InputString
      * L45: 000242     IF MyString NOT > SPACE
      * L46: 000243         INVOKE CLASS-ARGUMENTEXCEPTION "NEW"
      * L47: 000244         USING BY VALUE "Invalid Input Parameter"
      * L48: 000245         RETURNING MyException

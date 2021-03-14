from lark import Lark, Transformer
import time
import sys
import os
import traceback
import json

ifc_parser = Lark(r"""

file: "ISO-10303-21;" header data_section "END-ISO-10303-21;"

header: "HEADER" ";" header_comment? header_entity_list "ENDSEC" ";"

header_comment: header_comment_start header_line header_line* "*" (("*")* "/")+
header_comment_start: "/" "*" "*"* 
header_line: (SPECIAL|DIGIT|LCASE_LETTER|UCASE_LETTER)* "*"

data_section: "DATA" ";" (entity_instance)* "ENDSEC" ";"

entity_instance: simple_entity_instance|complex_entity_instance
simple_entity_instance: id "=" simple_record ";" 
complex_entity_instance: id "=" subsuper_record ";"
subsuper_record : "(" simple_record_list ")" 

simple_record_list:simple_record simple_record* 
simple_record: keyword "("parameter_list?")"

header_entity :keyword "(" parameter_list ")" ";" 
header_entity_list: header_entity header_entity* 

id: "#" DIGIT (DIGIT)*
keyword: ("A" .. "Z") ("A" .. "Z"|"_"|DIGIT)*

parameter: untyped_parameter|typed_parameter|omitted_parameter
parameter_list: parameter ("," parameter)*
list: "(" parameter ("," parameter)* ")" 
typed_parameter: keyword "(" parameter ")"|"()" 
untyped_parameter: string| NONE |INT |REAL |enumeration |id |binary |list
omitted_parameter: "*" 

enumeration: "." keyword "."

binary: "\"" ("0"|"1"|"2"|"3") (HEX)* "\"" 

string: "'" (SPECIAL|DIGIT|LCASE_LETTER|UCASE_LETTER|"\\*\\")* "'" 

WO:(LCASE_LETTER)*

NONE: "$"

SPECIAL : "!"  
        | "*"
        | "$" 
        | "%" 
        | "&" 
        | "." 
        | "#" 
        | "+" 
        | "," 
        | "-" 
        | "(" 
        | ")" 
        | "?" 
        | "/" 
        | "\\"
        | ":" 
        | ";" 
        | "<" 
        | "=" 
        | ">" 
        | "@" 
        | "[" 
        | "]" 
        | "{" 
        | "|" 
        | "}" 
        | "^" 
        | "`" 
        | "~"
        | "_"
        | "\""
        | "\"\""
        | "''"

real: REAL

REAL: SIGN?  DIGIT  (DIGIT)* "." (DIGIT)* ("E"  SIGN  DIGIT (DIGIT)* )?

INT: SIGN? DIGIT  (DIGIT)* 

HEX_FOUR: HEX_TWO HEX_TWO

HEX_TWO: HEX_ONE HEX_ONE 

HEX_ONE: HEX HEX

HEX:      "0" 
        | "1" 
        | "2" 
        | "3" 
        | "4" 
        | "5"
        | "6" 
        | "7" 
        | "8" 
        | "9" 
        | "A" 
        | "B" 
        | "C" 
        | "D" 
        | "E" 
        | "F" 


DIGIT: "0".."9"
SIGN: "+"|"-"
LCASE_LETTER: "a".."z"
UCASE_LETTER: "A".."Z"

ESCAPE    : "\\" ( "$" | "\"" | CHAR )
CHAR      : /[^$"\n]/
WORD      : CHAR+

WS: /[ \t\f\r\n]/+

%ignore WS
%ignore "\n"

""", parser='lalr', start='file')

 

if __name__ == "__main__":
        fn = ifc_fn = sys.argv[1]
        f = open(fn, "r")
        text = f.read() 
        jsonresultout = os.path.join(os.getcwd(), "result_syntax.json")
        start_time = time.time()

        try:
                tree = ifc_parser.parse(text)
                print("--- %s seconds ---" % (time.time() - start_time))
                print(tree.children[0])

                
        except Exception as lark_exception:
                import pdb;pdb.set_trace()
                traceback.print_exc(file=sys.stdout)
                # print("Unexpected error:", sys.exc_info())
        



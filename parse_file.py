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
header_line: (SPECIAL|DIGIT|LOWER|UPPER)* "*"
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
list: "(" parameter ("," parameter)* ")" |"("")"
typed_parameter: keyword "(" parameter ")"|"()" 
untyped_parameter: string| NONE |INT |REAL |enumeration |id |binary |list
omitted_parameter:STAR
STAR: "*" 
enumeration: "." keyword "."
binary: "\"" ("0"|"1"|"2"|"3") (HEX)* "\"" 
string: "'" (SPECIAL|DIGIT|LOWER|UPPER|"\\*\\")* "'" 

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



REAL: SIGN?  DIGIT  (DIGIT)* "." (DIGIT)* ("E"  SIGN?  DIGIT (DIGIT)* )?
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
LOWER: "a".."z"
UPPER: "A".."Z"
ESCAPE    : "\\" ( "$" | "\"" | CHAR )
CHAR      : /[^$"\n]/
WORD      : CHAR+
WS: /[ \t\f\r\n]/+

%ignore WS
%ignore "\n"

""", parser='lalr', start='file')

class Ref:
        def __init__(self, id):
                self.id = id
        def __str__(self):
                return '#' + str(self.id)
        __repr__ = __str__

class IfcType:
        def __init__(self, ifctype, value):
                self.ifctype = ifctype
                self.value = value
        def __str__(self):
                return self.ifctype + "(" + str(self.value) + ")"
        __repr__ = __str__

class T(Transformer):
        def id(self, s):
                num_list = [str(n) for n in s ]
                word = int("".join(num_list))
                return Ref(int("".join(num_list)))

        def string(self, s):
                word = "".join(s)
                return word

        def keyword(self, s):
                word = "".join(s)
                return word

        def untyped_parameter(self, s):
                return s[0]
        
  

        def parameter(self, s):
                return s[0]
        

        def typed_parameter(self, s):
                if len(s):
                        return IfcType(s[0], s[1])
                else:
                        return ()
 

        def omitted_parameter(self, s):
                return s[0]
        def enumeration(self, s):
                return s[0]

        parameter_list = tuple
        list = tuple
        subsuper_record = list
        INT = int
        REAL = float
        NONE = str
        STAR = str
        

def get_header(tree):
        return tree[0]

def process_attributes(attributes_tree):
        attributes = []
        at = attributes_tree
        return [a for a in at]
       
def create_step_entity(entity_tree):
        entity = {}
        t = T(visit_tokens=True).transform(entity_tree)
        id_tree = t.children[0].children[0]

        entity_id = t.children[0].children[0].id      
        entity_type = t.children[0].children[1].children[0]

        attributes_tree =  t.children[0].children[1].children[1]
        attributes = process_attributes(attributes_tree)

        return {'id':entity_id, 'type': entity_type, 'attributes':attributes}


def process_tree(file_tree):
        ents = {}
        
        n = len(file_tree.children[1].children)
        if n:
            percentages = [i * 100. / n for i in range(n+1)]
            num_dots = [int(b) - int(a) for a, b in zip(percentages, percentages[1:])]

        for idx, entity_tree in enumerate(file_tree.children[1].children):
                sys.stdout.write(num_dots[idx] * ".")
                sys.stdout.flush()
                ent = create_step_entity(entity_tree)
                ents[ent['id']] = ent

        return ents


if __name__ == "__main__":
        fn = ifc_fn = sys.argv[1]
        f = open(fn, "r")
        text = f.read() 
        jsonresultout = os.path.join(os.getcwd(), "result_syntax.json")
        start_time = time.time()
        
        try:
                tree = ifc_parser.parse(text)
                # print("--- %s seconds ---" % (time.time() - start_time))
                entities = process_tree(tree)
                print("valid", file=sys.stderr)
        except Exception as lark_exception:
                print(lark_exception, file=sys.stderr)
                



        



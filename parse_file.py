from lark import Lark, Transformer
import time
import sys
import os
import json
# import pdb; pdb.set_trace()
ifc_parser = Lark(r"""

file: "ISO-10303-21;" header data "END-ISO-10303-21;"

header: "HEADER" ";" filerecord* "ENDSEC" ";"

data: "DATA" ";" record* "ENDSEC" ";"
filerecord: filedecl attributes ";"
record: id "=" ifcclass attributes ";"
id: "#" (DIGIT)*
ifcclass:"IFC" IDENTIFIER
filedecl : "FILE_" IDENTIFIER

tup: "(" attribute ("," attribute)* ")" | "()"

attributes: "(" attribute ("," attribute)* ")" | "()" 

attribute:  STAR| NONE | INT | REAL | enumeration |id|ifcclass attributes|string |tup 

enumeration: "." (IDENTIFIER|"_")* "."

string: "'" (SPECIAL|DIGIT|LCASE_LETTER|UCASE_LETTER)* "'"


WO:(LCASE_LETTER)*
STAR: "*"
NONE: "$"
expansion : "$" IDENTIFIER

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

real: REAL
REAL: SIGN?  DIGIT  (DIGIT)* "." (DIGIT)* ("E"  SIGN  DIGIT (DIGIT)* )?
INT: SIGN? DIGIT  (DIGIT)* 
DIGIT: "0".."9"
SIGN: "+"|"-"

LCASE_LETTER: "a".."z"
UCASE_LETTER: "A".."Z"

IDENTIFIER: ("A" .. "Z" | "a" .. "z") ("A" .. "Z" | "a" .. "z" | "0" .. "9")*
ESCAPE    : "\\" ( "$" | "\"" | CHAR )
CHAR      : /[^$"\n]/
WORD      : CHAR+
HASHTAG : "#"

WS: /[ \t\f\r\n]/+
%ignore WS

%ignore "\n"

""", parser='lalr', start='file')


      
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
                return word
        def INT(self, s):
                num_list = [str(n) for n in s ]
                word = int("".join(num_list))
                return word
        def string(self, s):
                word = "".join(s)
                return word
        def enumeration(self, s):
                return s[0]

        def IDENTIFIER(self, s):
                word = "".join(s)
                return word

        INT = int
        REAL = float
        NONE = str
        STAR = str

def process_attributes(file_id, attributes_tree, tup=False):
        attributes = []
        relations = []
        
        for a in attributes_tree.children:
                try:     
                        if a.children[0].data == 'tup':
                                attributes.append(process_attributes(file_id, a.children[0], tup=True))
                        elif a.children[0].data == 'string' :
                                to_append = T(visit_tokens=True).transform(a)
                                attributes.append(to_append.children[0])
                        elif a.children[0].data == 'id' :
                                to_append = T(visit_tokens=True).transform(a)
                                attributes.append(to_append.children[0])
                                relations.append(to_append.children[0])
                                
                                if tup:
                                        # print(file_id, to_append.children[0])
                                        rels.append((file_id, to_append.children[0],))

                                        if file_id in drels.keys():
                                                drels[file_id].append(to_append.children[0])
                                        else:
                                                drels[file_id] = [to_append.children[0]]

                        elif a.children[0].data == 'enumeration' :
                                # attributes.append(a.children[0].children[0])
                                to_append = T(visit_tokens=True).transform(a).children[0]
                                attributes.append(to_append)
                        elif a.children[0].data == 'ifcclass' :
                                attributes.append(create_entity(a, is_attr=1))
                        else:  
                                attributes.append(a)
                except:
                        # When the tree contains a Token. Todo: more robust way to 
                        # handle that case. 
                        attributes.append(T(visit_tokens=True).transform(a).children[0])

        if tup:
                return tuple(attributes)
        else:
                return attributes,relations



def create_entity(record, is_attr=False):
        if is_attr:              
                ifc_type = "IFC"+record.children[0].children[0]
   
                a = record.children[1].children[0]
                val = T(visit_tokens=True).transform(a).children[0]

                return IfcType(ifc_type, val)
        else:
                id_tree = record.children[0]
                file_id = T(visit_tokens=True).transform(id_tree)
                
                ifc_type = "IFC" + record.children[1].children[0]
                attributes_tree = record.children[2]
                attributes = process_attributes(file_id, attributes_tree)

                return {'id':file_id, 'ifc_type':ifc_type, 'attributes':attributes }



fn = "files/acad2010_walls.ifc"
fn = ifc_fn = sys.argv[1]
f = open(fn, "r")
text = f.read() 
jsonresultout = os.path.join(os.getcwd(), "result_syntax.json")
start_time = time.time()

try:
        tree = ifc_parser.parse(text)



        print("--- %s seconds ---" % (time.time() - start_time))

        header = tree.children[0]

        for filerecord in header.children:
                if filerecord.children[0].children[0] == 'SCHEMA':
                        schema_tree = filerecord.children[1]
                        schema_string = schema_tree.children[0].children[0].children[0].children[0]
                        char_list = [c[0] for c in schema_string.children ]
                        schema = "".join(char_list)     

        data = tree.children[1]

        test_record = data.children[0]


        rels = []

        drels = {}


        ents = {}

        for r in data.children:
                entity = create_entity(r)
                ents[entity['id']] = entity


        for e in ents.values():
                if e['id'] in drels.keys():
                        e['attributes'][1].extend(drels[e['id']])

        with open(jsonresultout, 'w', encoding='utf-8') as f:
                json.dump({'syntax':'v'}, f, ensure_ascii=False, indent=4)



except:
        
        
        with open(jsonresultout, 'w', encoding='utf-8') as f:
                json.dump({'syntax':'i'}, f, ensure_ascii=False, indent=4)




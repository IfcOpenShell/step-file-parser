from collections import namedtuple

grammar = r"""
file: "ISO-10303-21;" header data_section "END-ISO-10303-21;"
header: "HEADER" ";" header_entity_list "ENDSEC" ";"
header_line: (SPECIAL|DIGIT|LOWER|UPPER)* "*"
data_section: "DATA" ";" (entity_instance)* "ENDSEC" ";"
entity_instance: simple_entity_instance|complex_entity_instance 
simple_entity_instance: id "=" simple_record ";" 
complex_entity_instance: id "=" subsuper_record ";"
subsuper_record : "(" simple_record_list ")" 
simple_record_list:simple_record simple_record* 
simple_record: keyword "("parameter_list?")"
header_entity_list: file_description file_name file_schema
file_description: "FILE_DESCRIPTION" "(" parameter_list ")" ";"
file_name: "FILE_NAME" "(" parameter_list ")" ";"
file_schema: "FILE_SCHEMA" "(" parameter_list ")" ";"
id: /#[0-9]+/
keyword: /[A-Z][0-9A-Z_]*/
parameter: untyped_parameter|typed_parameter|omitted_parameter
parameter_list: parameter ("," parameter)*
list: "(" parameter ("," parameter)* ")" |"("")"
typed_parameter: keyword "(" parameter ")"|"()" 
untyped_parameter: string| NONE |INT |REAL |enumeration |id |binary |list
omitted_parameter:STAR
enumeration: "." keyword "."
binary: "\"" ("0"|"1"|"2"|"3") (HEX)* "\"" 
string: "'" (REVERSE_SOLIDUS REVERSE_SOLIDUS|SPECIAL|DIGIT|SPACE|LOWER|UPPER|CONTROL_DIRECTIVE|"\\*\\")* "'"

STAR: "*"
SLASH: "/"
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
CONTROL_DIRECTIVE: PAGE | ALPHABET | EXTENDED2 | EXTENDED4 | ARBITRARY 
PAGE : REVERSE_SOLIDUS "S" REVERSE_SOLIDUS LATIN_CODEPOINT
LATIN_CODEPOINT : SPACE | DIGIT | LOWER | UPPER | SPECIAL | REVERSE_SOLIDUS | APOSTROPHE
ALPHABET : REVERSE_SOLIDUS "P" UPPER REVERSE_SOLIDUS 
EXTENDED2: REVERSE_SOLIDUS "X2" REVERSE_SOLIDUS (HEX_TWO)* END_EXTENDED 
EXTENDED4 :REVERSE_SOLIDUS "X4" REVERSE_SOLIDUS (HEX_FOUR)* END_EXTENDED 
END_EXTENDED: REVERSE_SOLIDUS "X0" REVERSE_SOLIDUS 
ARBITRARY: REVERSE_SOLIDUS "X" REVERSE_SOLIDUS HEX_ONE 
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
APOSTROPHE: "'"
REVERSE_SOLIDUS: "\\"
DIGIT: "0".."9"
SIGN: "+"|"-"
LOWER: "a".."z"
UPPER: "A".."Z"
ESCAPE    : "\\" ( "$" | "\"" | CHAR )
CHAR      : /[^$"\n]/
WORD      : CHAR+
SPACE.10  : " "

%ignore /[ \t\f\r\n]/+
"""

HEADER_FIELDS = {
    "file_description": namedtuple('file_description', ['description', 'implementation_level']),
    "file_name": namedtuple('file_name', ['name', 'time_stamp', 'author', 'organization', 'preprocessor_version', 'originating_system', 'authorization']),
    "file_schema":  namedtuple('file_schema', ['schema_identifiers']),
}
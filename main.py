import time
import sys
import os
import traceback
import json

from collections import defaultdict

from lark import Lark, Transformer, Tree, Token
from lark.exceptions import UnexpectedToken


class ValidationError(Exception):
    pass


class SyntaxError(ValidationError):
    def __init__(self, filecontent, exception):
        self.filecontent = filecontent
        self.exception = exception
        
    def __str__(self, linewidth=80):
        ln = self.filecontent.split("\n")[self.exception.line-1]
        if len(self.exception.accepts) == 1:
            exp = next(iter(self.exception.accepts))
        else:
            exp = f"one of {' '.join(sorted(x for x in self.exception.accepts if '__ANON' not in x))}"
        return f"On line {self.exception.line} column {self.exception.column}:\nUnexpected {self.exception.token.type.lower()} ('{self.exception.token.value}')\nExpecting {exp}\n{self.exception.line:05d} | {ln}\n        {' ' * (self.exception.column - 1)}^"


class DuplicateNameError(ValidationError):
    def __init__(self, filecontent, name, linenumbers):
        self.name = name
        self.filecontent = filecontent
        self.linenumbers = linenumbers
        
    def __str__(self, linewidth=80):
        splitted = self.filecontent.split("\n")
        def build():
            max_line = 0
            yield f"On line {self.linenumbers[0]}:\nDuplicate instance name #{self.name}"
            for i in range(self.linenumbers[0] - 1, self.linenumbers[1]):
                yield f"{i+1:05d} | {splitted[i]}"
                max_line = max(max_line, len(splitted[i]))
            yield ' '* 8 + '^' * max_line
        return "\n".join(build())

grammar = r"""
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
string: "'" (SPECIAL|DIGIT|LOWER|UPPER|"\\*\\")* "'" 

COMMENT: SLASH STAR (SPECIAL|DIGIT|LOWER|UPPER|" ")* STAR SLASH
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

%ignore COMMENT
%ignore WS
%ignore "\n"
"""

class Ref:
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return "#" + str(self.id)

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
        num_list = [str(n) for n in s]
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


def create_step_entity(entity_tree):
    entity = {}
    t = T(visit_tokens=True).transform(entity_tree)
    
    def get_line_number(t):
        if isinstance(t, Token):
            yield t.line
    
    def traverse(fn, x):
        yield from fn(x)
        if isinstance(x, Tree):
            for c in x.children:
                yield from traverse(fn, c)
                
    lines = list(traverse(get_line_number, entity_tree))

    id_tree = t.children[0].children[0]

    entity_id = t.children[0].children[0].id
    entity_type = t.children[0].children[1].children[0]

    attributes_tree = t.children[0].children[1].children[1]
    attributes = list(attributes_tree)

    return {"id": entity_id, "type": entity_type, "attributes": attributes, "lines": (min(lines), max(lines))}


def process_tree(filecontent, file_tree, with_progress):
    ents = defaultdict(list)

    n = len(file_tree.children[1].children)
    if n:
        percentages = [i * 100.0 / n for i in range(n + 1)]
        num_dots = [int(b) - int(a) for a, b in zip(percentages, percentages[1:])]

    for idx, entity_tree in enumerate(file_tree.children[1].children):
        if with_progress:
            sys.stdout.write(num_dots[idx] * ".")
            sys.stdout.flush()
        ent = create_step_entity(entity_tree)
        id_ = int(ent["id"])
        if ents[id_]:
            raise DuplicateNameError(filecontent, ent['id'], ent['lines'])
        ents[id_].append(ent)
    
    return ents


def parse(*, filename=None, filecontent=None, with_progress=False, with_tree=True):
    if filename:
        assert not filecontent
        filecontent = open(filename, encoding='ascii').read()
        
    transformer = {}
    if not with_tree:
        # If we're not going to return the tree, we also don't need to
        # keep in memory while parsing. So we build a transformer that
        # just returns None for every rule. lark creates a dictionary
        # of callbacks from the transformer type object, so we can't
        # simply use __getattr__ we need an actual type objects with
        # callback functions for the rules given in the grammar.
        
        # Create a temporary parser just for analysing the grammar
        temp = Lark(grammar, parser="lalr", start="file")
        # Extract the rule names
        rule_names = filter(lambda s: not s.startswith('_'), set(r.origin.name for r in temp.rules))
        null_function = lambda *args: None
        NT = type('NullTransformer', (Transformer,), {r: null_function for r in rule_names})
        transformer = {'transformer': NT}

    parser = Lark(grammar, parser="lalr", start="file", **transformer)
    
    try:
        ast = parser.parse(filecontent)
    except UnexpectedToken as e:
        raise SyntaxError(filecontent, e)
    
    if with_tree:
        return process_tree(filecontent, ast, with_progress)
     

if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("-")]
    flags = [x for x in sys.argv[1:] if x.startswith("-")]
    
    fn = sys.argv[1]
    jsonresultout = os.path.join(os.getcwd(), "result_syntax.json")
    start_time = time.time()

    try:
        parse(filename=fn, with_progress="--progress" in flags, with_tree=False)
        print("Valid", file=sys.stderr)
        exit(0)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        exit(1)

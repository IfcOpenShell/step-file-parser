import builtins
from dataclasses import dataclass
import itertools
import numbers
import sys
import re

from collections import defaultdict
import types

from lark import Lark, Transformer, Tree, Token
from lark.exceptions import UnexpectedToken, UnexpectedCharacters
try:
    from .mvd_info import MvdInfo, LARK_AVAILABLE
except ImportError: # in case of running module locally (e.g. test_parser.py)
    from mvd_info import MvdInfo, LARK_AVAILABLE

class ValidationError(Exception):
    pass

from collections import namedtuple

class SyntaxError(ValidationError):
    def __init__(self, filecontent, exception):
        self.filecontent = filecontent
        self.exception = exception

    def asdict(self, with_message=True):
        return {
            "type": (
                "unexpected_token"
                if isinstance(self.exception, UnexpectedToken)
                else "unexpected_character"
            ),
            "lineno": self.exception.line,
            "column": self.exception.column,
            "found_type": self.exception.token.type.lower(),
            "found_value": self.exception.token.value,
            "expected": sorted(x for x in self.exception.accepts if "__ANON" not in x),
            "line": self.filecontent.split("\n")[self.exception.line - 1],
            **({"message": str(self)} if with_message else {}),
        }

    def __str__(self):
        d = self.asdict(with_message=False)
        if len(d["expected"]) == 1:
            exp = d["expected"][0]
        else:
            exp = f"one of {' '.join(d['expected'])}"

        sth = "character" if d["type"] == "unexpected_character" else ""

        return f"On line {d['lineno']} column {d['column']}:\nUnexpected {sth}{d['found_type']} ('{d['found_value']}')\nExpecting {exp}\n{d['lineno']:05d} | {d['line']}\n        {' ' * (self.exception.column - 1)}^"


class DuplicateNameError(ValidationError):
    def __init__(self, filecontent, name, linenumbers):
        self.name = name
        self.filecontent = filecontent
        self.linenumbers = linenumbers

    def asdict(self, with_message=True):
        return {
            "type": "duplicate_name",
            "name": self.name,
            "lineno": self.linenumbers[0],
            "line": self.filecontent.split("\n")[self.linenumbers[0] - 1],
            **({"message": str(self)} if with_message else {}),
        }

    def __str__(self):
        d = self.asdict(with_message=False)

        def build():
            yield f"On line {d['lineno']}:\nDuplicate instance name #{d['name']}"
            yield f"{d['lineno']:05d} | {d['line']}"
            yield " " * 8 + "^" * len(d["line"].rstrip())

        return "\n".join(build())


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
file_description: "FILE_DESCRIPTION" "(" parameter "," parameter ")" ";"
file_name: "FILE_NAME" "(" parameter "," parameter "," parameter "," parameter "," parameter "," parameter "," parameter ")" ";"
file_schema: "FILE_SCHEMA" "(" parameter ")" ";"
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
        return int(s[0][1:])

    def string(self, s):
        word = "".join(s).replace("''", "'")
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
    NONE = lambda *args: None
    STAR = str


@dataclass
class entity_instance:
    id: int
    type: str
    attributes: tuple
    lines: tuple

    def __getitem__(self, k):
        if isinstance(k, numbers.Integral):
            return self.attributes[k]
        else:
            # compatibility with dict
            return getattr(self, k)

    def __repr__(self):
        return f'#{self.id}={self.type}({",".join(map(str, self.attributes))})'


def create_step_entity(entity_tree):
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

    entity_id = t.children[0].children[0]
    entity_type = t.children[0].children[1].children[0]

    attributes_tree = t.children[0].children[1].children[1]
    attributes = list(attributes_tree)

    return entity_instance(
        entity_id,
        entity_type,
        attributes,
        (min(lines), max(lines)),
    )
    
def make_header_ent(ast):
    rule = ast.data
    params = T(visit_tokens=True).transform(ast.children[0])
    return rule.upper(), params



def process_tree(filecontent, file_tree, with_progress, with_header=False):
    ents = defaultdict(list)
    header, data = file_tree.children

    if with_header:
        header = dict(map(make_header_ent, header.children[0].children))

    n = len(data.children)
    if n:
        percentages = [i * 100.0 / n for i in range(n + 1)]
        num_dots = [int(b) - int(a) for a, b in zip(percentages, percentages[1:])]

    for idx, entity_tree in enumerate(data.children):
        if with_progress:
            sys.stdout.write(num_dots[idx] * ".")
            sys.stdout.flush()
        ent = create_step_entity(entity_tree)
        id_ = int(ent["id"])
        if ents[id_]:
            raise DuplicateNameError(filecontent, ent["id"], ent["lines"])
        ents[id_].append(ent)

    if with_header:
        return header, ents
    else:
        return ents


def parse(
    *,
    filename=None,
    filecontent=None,
    with_progress=False,
    with_tree=True,
    with_header=False,
    only_header=False
):
    if filename:
        assert not filecontent
        filecontent = builtins.open(filename, encoding=None).read()
        
    if only_header:
        assert with_header, "'only_header=True' requires 'with_header=True'"

    # Match and remove the comments
    p = r"/\*[\s\S]*?\*/"

    def replace_fn(match):
        return re.sub(r"[^\n]", " ", match.group(), flags=re.M)

    filecontent_wo_comments = re.sub(p, replace_fn, filecontent)
    
        
    if only_header:
        # Extract just the HEADER section using regex
        header_match = re.search(
            r"ISO-10303-21;\s*HEADER;(.*?)ENDSEC;",
            filecontent_wo_comments,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if not header_match:
            raise ValidationError("No HEADER section found in file")

        header_text = f"HEADER;{header_match.group(1)}ENDSEC;"
        full_header_text = f"ISO-10303-21;{header_text}DATA;ENDSEC;END-ISO-10303-21;"

        parser = Lark(grammar, parser="lalr", start="file")
        try:
            ast = parser.parse(full_header_text)
        except (UnexpectedToken, UnexpectedCharacters) as e:
            raise SyntaxError(filecontent, e)

        header_tree = ast.children[0]  # HEADER section

        header = dict(map(make_header_ent, header_tree.children[0].children))
        return header
    

    instance_identifiers = []
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
        rule_names = filter(
            lambda s: not s.startswith("_"), set(r.origin.name for r in temp.rules)
        )
        null_function = lambda self, *args: None
        # Create dictionary of methods for type() creation
        methods = {r: null_function for r in rule_names}

        # Even in this case we do want to report duplicate identifiers
        # so these need to be captured
        methods["id"] = lambda self, *args: args
        methods["simple_entity_instance"] = (
            lambda self, tree: instance_identifiers.append(
                (int(tree[0][0][0][1:]), int(tree[0][0][0].line))
            )
        )

        NT = type("NullTransformer", (Transformer,), methods)
        transformer = {"transformer": NT()}

    parser = Lark(grammar, parser="lalr", start="file", **transformer)

    try:
        ast = parser.parse(filecontent_wo_comments)
    except (UnexpectedToken, UnexpectedCharacters) as e:
        raise SyntaxError(filecontent, e)

    if with_tree:
        return process_tree(filecontent, ast, with_progress, with_header)
    else:
        # process_tree() would take care of duplicate identifiers,
        # but we need to do it ourselves now using our rudimentary
        # transformer
        seen = set()
        for iden, lineno in instance_identifiers:
            if iden in seen:
                raise DuplicateNameError(filecontent, iden, [lineno, lineno])
            seen.add(iden)


class file:
    """
    A somewhat compatible interface (but very limited) to ifcopenshell.file
    """

    def __init__(self, parse_outcomes):
        self.header_, self.data_ = parse_outcomes

    @property
    def schema_identifier(self) -> str:
        return self.header_["FILE_SCHEMA"][0][0]

    @property
    def schema(self) -> str:
        """General IFC schema version: IFC2X3, IFC4, IFC4X3."""
        prefixes = ("IFC", "X", "_ADD", "_TC")
        reg = "".join(f"(?P<{s}>{s}\\d+)?" for s in prefixes)
        match = re.match(reg, self.schema_identifier)
        version_tuple = tuple(
            map(
                lambda pp: int(pp[1][len(pp[0]) :]) if pp[1] else None,
                ((p, match.group(p)) for p in prefixes),
            )
        )
        return "".join(
            "".join(map(str, t)) if t[1] else ""
            for t in zip(prefixes, version_tuple[0:2])
        )

    @property
    def schema_version(self) -> tuple[int, int, int, int]:
        """Numeric representation of the full IFC schema version.

        E.g. IFC4X3_ADD2 is represented as (4, 3, 2, 0).
        """
        schema = self.wrapped_data.schema
        version = []
        for prefix in ("IFC", "X", "_ADD", "_TC"):
            number = re.search(prefix + r"(\d)", schema)
            version.append(int(number.group(1)) if number else 0)
        return tuple(version)


    @property
    def header(self):
        HEADER_FIELDS = {
            "file_description": namedtuple('file_description', ['description', 'implementation_level']),
            "file_name": namedtuple('file_name', ['name', 'time_stamp', 'author', 'organization', 'preprocessor_version', 'originating_system', 'authorization']),
            "file_schema":  namedtuple('file_schema', ['schema_identifiers']),
        }
        header = {}

        for field_name, namedtuple_class in HEADER_FIELDS.items():
            field_data = self.header_.get(field_name.upper(), [])
            header[field_name.lower()] = namedtuple_class(*field_data)

        return types.SimpleNamespace(**header)
    
    
    @property
    def mvd(self):
        if not LARK_AVAILABLE or MvdInfo is None:
            return None
        return MvdInfo(self.header)

    def __getitem__(self, key: numbers.Integral) -> entity_instance:
        return self.by_id(key)

    def by_id(self, id: int) -> entity_instance:
        """Return an IFC entity instance filtered by IFC ID.

        :param id: STEP numerical identifier
        :type id: int

        :raises RuntimeError: If `id` is not found or multiple definitions exist for `id`.

        :rtype: entity_instance
        """
        ns = self.data_.get(id, [])
        if len(ns) == 0:
            raise RuntimeError(f"Instance with id {id} not found")
        elif len(ns) > 1:
            raise RuntimeError(f"Duplicate definition for id {id}")
        return ns[0]

    def by_type(self, type: str) -> list[entity_instance]:
        """Return IFC objects filtered by IFC Type and wrapped with the entity_instance class.
        :rtype: list[entity_instance]
        """
        type_lc = type.lower()
        return list(
            filter(
                lambda ent: ent.type.lower() == type_lc,
                itertools.chain.from_iterable(self.data_.values()),
            )
        )


def open(fn, only_header: bool = False) -> file:
    if only_header: # Ensure consistent options
        parse_outcomes = parse(
            filename=fn,
            with_tree=True,
            with_header=True,  # must be True to return the header
            only_header=True,
        )
        return file((parse_outcomes, defaultdict(list)))  # data section is empty
    else:
        parse_outcomes = parse(
            filename=fn,
            with_tree=True,
            with_header=True,
            only_header=False,
        )
        return file(parse_outcomes)
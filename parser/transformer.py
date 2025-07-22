from lark import Transformer
from dataclasses import dataclass
import numbers
from lark import Lark, Transformer, Tree, Token


class IfcType:
    def __init__(self, ifctype, value):
        self.ifctype = ifctype
        self.value = value

    def __str__(self):
        return self.ifctype + "(" + str(self.value) + ")"

    __repr__ = __str__

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

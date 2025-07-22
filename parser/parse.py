from dataclasses import dataclass
from collections import defaultdict
import re 
import sys
import builtins
from lark import Lark, UnexpectedCharacters, UnexpectedToken

# import transformer
from .transformer import Transformer, entity_instance, make_header_ent, create_step_entity
from .grammar import grammar, HEADER_FIELDS
from .errors import HeaderFieldError, DuplicateNameError, ErrorCollector, ValidationError, SyntaxError

def validate_header_fields(header, error_collector, only_header = False):
    for field in HEADER_FIELDS.keys():
        observed = header.get(field.upper(), [])
        expected = HEADER_FIELDS.get(field)._fields
        if len(observed) != len(expected):
            error_collector.add(HeaderFieldError(field.upper(), len(observed), len(expected)))
            if only_header:
                error_collector.raise_if_any()

@dataclass
class ParseResult:
    header: dict
    entities: dict[int, list[entity_instance]]
    

def process_tree(filecontent, file_tree, with_progress, error_collector):
    ents = defaultdict(list)
    header, data = file_tree.children

    header = dict(map(make_header_ent, header.children[0].children))
    validate_header_fields(header, error_collector)

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
            error_collector.add(DuplicateNameError(filecontent, ent["id"], ent["lines"]))
        else:
            ents[id_].append(ent)

    return header, ents

def parse(
    *,
    filename=None,
    filecontent=None,
    with_progress=False,
    with_tree=True,
    only_header=False,
) -> ParseResult:
    error_collector = ErrorCollector()
    if filename:
        assert not filecontent
        filecontent = builtins.open(filename, encoding=None).read()

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
            error_collector.add(HeaderFieldError(
                'header', '', 'No HEADER section found in file'
            ))
            error_collector.raise_if_any()

        header_text = f"HEADER;{header_match.group(1)}ENDSEC;"
        full_header_text = f"ISO-10303-21;{header_text}DATA;ENDSEC;END-ISO-10303-21;"

        parser = Lark(grammar, parser="lalr", start="file")
        try:
            ast = parser.parse(full_header_text)
        except (UnexpectedToken, UnexpectedCharacters) as e:
            error_collector.add(SyntaxError(filecontent, e))
            error_collector.raise_if_any()  # Immediately abort in case of critical error


        header_tree = ast.children[0]  # HEADER section

        header = dict(map(make_header_ent, header_tree.children[0].children))
        validate_header_fields(header, error_collector, only_header=True)
        error_collector.raise_if_any() 
        return ParseResult(
            header = header,
            entities = defaultdict(list)
        )
    

    instance_identifiers = []
    transformer = {}
    if not with_tree:
        # If we're not going to return the tree, we also don't need to
        # keep in memory while parsing. So we build a transformer that
        # just returns None for every rule. lark creates a dictionary
        # of callbacks from the transformer type object, so we can't
        # simply use __getattr__ we need an actual type objects with
        # callback functions for the rules given in the 

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
        error_collector.add(SyntaxError(filecontent, e))
        error_collector.raise_if_any()  # Immediately abort in case of critical error

    if with_tree:
        header, data = process_tree(filecontent, ast, with_progress, error_collector)
        error_collector.raise_if_any() 
        return ParseResult(
            header = header, 
            entities = data
        )
    else:
        # process_tree() would take care of duplicate identifiers,
        # but we need to do it ourselves now using our rudimentary
        # transformer
        seen = set()
        for iden, lineno in instance_identifiers:
            if iden in seen:
                error_collector.add(DuplicateNameError(filecontent, iden, [lineno, lineno]))
            else:
                seen.add(iden)
        error_collector.raise_if_any()

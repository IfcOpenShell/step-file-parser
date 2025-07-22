from lark.exceptions import UnexpectedToken

class ValidationError(Exception):
    pass

class ErrorCollector:
    def __init__(self):
        self.errors = []

    def add(self, error):
        self.errors.append(error)

    def raise_if_any(self):
        if self.errors:
            raise CollectedValidationErrors(self.errors)

class CollectedValidationErrors(ValidationError):
    def __init__(self, errors):
        self.errors = errors
        
    def asdict(self, with_message=True):
        return [e.asdict(with_message=with_message) for e in self.errors]

    def __str__(self):
        return f"{len(self.errors)} validation error(s) collected:\n" + "\n\n".join(str(e) for e in self.errors)

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
    
    
class HeaderFieldError(ValidationError):
    def __init__(self, field, found_len, expected_len):
        self.field = field
        self.found_len = found_len
        self.expected_len = expected_len

    def asdict(self, with_message=True):
        return {
            "type": "invalid_header_field",
            "field": self.field,
            "expected_field_count": self.expected_len,
            "actual_field_count": self.found_len,
            **({"message": str(self)} if with_message else {}),
        }

    def __str__(self):
        return (
            f"Invalid number of parameters for HEADER field '{self.field}'. "
            f"Expected {self.expected_len}, found {self.found_len}."
        )
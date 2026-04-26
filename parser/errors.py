from typing import Any, Optional

from lark.exceptions import UnexpectedToken, UnexpectedCharacters


class _ValidationError(Exception):
    def __init__(self, *args, **kwargs):
        if self.__class__ is _ValidationError:
            raise TypeError("Do not raise _ValidationError directly.")
        super().__init__(*args, **kwargs)


class ErrorCollector:
    def __init__(self):
        self.errors = []

    def add(self, error):
        self.errors.append(error)

    def raise_if_any(self):
        if self.errors:
            raise CollectedValidationErrors(self.errors)


class CollectedValidationErrors(_ValidationError):
    def __init__(self, errors):
        self.errors = errors

    def asdict(self, with_message=True):
        return [e.asdict(with_message=with_message) for e in self.errors]

    def __str__(self):
        return f"{len(self.errors)} validation error(s) collected:\n" + "\n\n".join(
            str(e) for e in self.errors
        )


class SyntaxError(_ValidationError):
    def __init__(self, filecontent, exception):
        self.filecontent = filecontent
        self.exception = exception

    def asdict(self, with_message=True):
        def get_type_token_and_expected(exc: Exception) -> tuple[str, str, str, list]:
            match (exc):
                case UnexpectedToken():
                    return (
                        "unexpected_token",
                        exc.token.type.lower(),
                        exc.token.value,
                        sorted(x for x in self.exception.accepts if "__ANON" not in x),
                    )
                case UnexpectedCharacters():
                    return "unexpected_character", "character", hex(ord(exc.char)), []
                case _:
                    raise TypeError(f"Unexpected exception type {type(exc)}")

        exception_type, token_type, token_value, expected = get_type_token_and_expected(
            self.exception
        )

        return {
            "type": exception_type,
            "lineno": self.exception.line,
            "column": self.exception.column,
            "found_type": token_type,
            "found_value": token_value,
            "expected": expected,
            "line": self.filecontent.split("\n")[self.exception.line - 1],
            **({"message": str(self)} if with_message else {}),
        }

    def __str__(self):
        d = self.asdict(with_message=False)
        if len(d["expected"]) == 1:
            exp = d["expected"][0]
        else:
            exp = f"one of {' '.join(d['expected'])}"

        return f"On line {d['lineno']} column {d['column']}:\nUnexpected {d['found_type']} ('{d['found_value']}')\nExpecting {exp}\n{d['lineno']:05d} | {d['line']}\n        {' ' * (self.exception.column - 1)}^"


class DuplicateNameError(_ValidationError):
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


class HeaderFieldError(_ValidationError):
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


class InvalidNameError(_ValidationError):
    def __init__(self, filecontent, name, linenumbers):
        self.name = name
        self.filecontent = filecontent
        self.linenumbers = linenumbers

    def asdict(self, with_message=True):
        return {
            "type": "invalid_name",
            "name": self.name,
            "lineno": self.linenumbers[0],
            "line": self.filecontent.split("\n")[self.linenumbers[0] - 1],
            **({"message": str(self)} if with_message else {}),
        }

    def __str__(self):
        d = self.asdict(with_message=False)

        def build():
            yield f"On line {d['lineno']}:\nInvalid instance name #{d['name']}"
            yield f"{d['lineno']:05d} | {d['line']}"
            yield " " * 8 + "^" * len(d["line"].rstrip())

        return "\n".join(build())

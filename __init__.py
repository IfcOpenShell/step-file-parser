try:
    from parser.parse import parse
    from parser.file import file, open
    from parser.errors import (
        _ValidationError,
        CollectedValidationErrors,
        DuplicateNameError,
        HeaderFieldError,
        InvalidNameError,
    )
except ImportError:
    from .parser.parse import parse
    from .parser.file import file, open
    from .parser.errors import (
        _ValidationError,
        CollectedValidationErrors,
        DuplicateNameError,
        HeaderFieldError,
        InvalidNameError,
    )

__all__ = [
    "parse",
    "open",
    "file",
    "_ValidationError",
    "CollectedValidationErrors",
    "DuplicateNameError",
    "HeaderFieldError",
    "InvalidNameError",
]  # for testing

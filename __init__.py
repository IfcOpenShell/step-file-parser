try:
    from parser.parse import parse
    from parser.file import file, open
    from parser.errors import ValidationError, CollectedValidationErrors, DuplicateNameError, HeaderFieldError
except:
    from .parser.parse import parse 
    from .parser.file import file, open 
    from .parser.errors import ValidationError, CollectedValidationErrors, DuplicateNameError, HeaderFieldError

__all__ = ["parse", "open", "file", "ValidationError", 
           "CollectedValidationErrors", "DuplicateNameError", "HeaderFieldError"] # for testing 
import glob
import pytest

from __init__ import parse, ValidationError
from contextlib import nullcontext


def create_context(fn):
    if "fail_" in fn:
        return pytest.raises(ValidationError)
    else:
        return nullcontext()


@pytest.mark.parametrize("file", glob.glob("fixtures/*.ifc"))
def test_file_with_tree(file):
    with create_context(file):
        parse(filename=file, with_tree=True)


@pytest.mark.parametrize("file", glob.glob("fixtures/*.ifc"))
def test_file_without_tree(file):
    with create_context(file):
        parse(filename=file, with_tree=False)

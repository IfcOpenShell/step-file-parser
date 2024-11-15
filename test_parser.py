import glob
import pytest

from __init__ import parse, open, ValidationError
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


def test_parse_features():
    f = open('fixtures/pass_1.ifc')
    assert f.by_id(1).id == 1
    assert f.by_id(1).type == 'IFCPERSON'
    assert f.by_type('ifcperson')[0].id == 1
    assert f[1][0] is None
    assert f.header.file_description[0][0] == 'ViewDefinition [CoordinationView]'
    assert f.by_type('ifcapplication')[1][2] == "Nested ' quotes"

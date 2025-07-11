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
    if "fail_too_many_header_entity_fields.ifc" in file:
        pytest.skip("This file relies on header field validation using the parsed AST, "
                "but with_tree=False uses a NullTransformer that discards the AST, "
                "so validating the header field names is not possible in this mode.")
    with create_context(file):
        parse(filename=file, with_tree=False)


def test_parse_features():
    f = open('fixtures/pass_1.ifc')
    assert f.by_id(1).id == 1
    assert f.by_id(1).type == 'IFCPERSON'
    assert f.data_[1][0].type == 'IFCPERSON'
    assert f.by_type('ifcperson')[0].id == 1
    assert f[1][0] is None
    assert f.header.file_description[0][0] == 'ViewDefinition [CoordinationView]'
    assert f.header_.get('FILE_DESCRIPTION')[0][0]
    assert f.by_type('ifcapplication')[1][2] == "Nested ' quotes"


def test_parse_valid_header():
    f = open('fixtures/passing_header.ifc')

    expected_description = {
        "description": ('ViewDefinition [Alignment-basedView]',),
        "implementation_level": '2;1',
    }

    expected_name = {
        "name": 'Header example2.ifc',
        "time_stamp": '2022-09-16T10:35:07',
        "author": ('Evandro Alfieri',),
        "organization": ('buildingSMART Int.',),
        "preprocessor_version": 'IFC Motor 1.0',
        "originating_system": 'Company - Application - 26.0.0.0',
        "authorization": 'none',
    }

    expected_schema = {
        "schema_identifiers": ('IFC4X3_ADD2',),
    }

    for key, val in expected_description.items():
        assert getattr(f.header.file_description, key) == val, f"{key} mismatch"

    for key, val in expected_name.items():
        assert getattr(f.header.file_name, key) == val, f"{key} mismatch"

    for key, val in expected_schema.items():
        assert getattr(f.header.file_schema, key) == val, f"{key} mismatch"
        

def test_header_only_api():
    f = open('fixtures/passing_header.ifc', only_header=True)
    expected_description = {
        "description": ('ViewDefinition [Alignment-basedView]',),
        "implementation_level": '2;1',
    }

    expected_name = {
        "name": 'Header example2.ifc',
        "time_stamp": '2022-09-16T10:35:07',
        "author": ('Evandro Alfieri',),
        "organization": ('buildingSMART Int.',),
        "preprocessor_version": 'IFC Motor 1.0',
        "originating_system": 'Company - Application - 26.0.0.0',
        "authorization": 'none',
    }

    expected_schema = {
        "schema_identifiers": ('IFC4X3_ADD2',),
    }

    for key, val in expected_description.items():
        assert getattr(f.header.file_description, key) == val, f"{key} mismatch"

    for key, val in expected_name.items():
        assert getattr(f.header.file_name, key) == val, f"{key} mismatch"

    for key, val in expected_schema.items():
        assert getattr(f.header.file_schema, key) == val, f"{key} mismatch"

def test_file_mvd_attr():
    f = open('fixtures/extended_mvd.ifc', only_header=True)
    
    assert 'ReferenceView_V1.2' in f.mvd.view_definitions
    assert all(i in f.mvd.keywords for i in ['exchange_requirements', 'view_definitions', 'remark', 'comments'])
    assert 'Ramp' in f.mvd.options['ExcludedObjects']
    assert f.mvd.Remark['SomeKey'] == 'SomeValue'
    assert len(f.mvd.comments) == 2
    assert all(v in vars(f.header).keys() for v in ['file_description', 'file_name', 'file_schema'])
    assert len(f.header.file_name) == 7


@pytest.mark.parametrize("filename", [
    'fixtures/fail_invalid_header_entity.ifc',
    'fixtures/fail_no_header.ifc',
])
def test_invalid_headers_(filename):
    # error in header
    with pytest.raises(ValidationError):
        parse(filename=filename, with_tree=False, only_header=True)

@pytest.mark.parametrize("filename", [
    'fixtures/fail_duplicate_id.ifc',
    'fixtures/fail_double_comma.ifc',
    'fixtures/fail_double_semi.ifc'
])
def test_valid_headers(filename):
    # error in body
    with nullcontext():
        parse(filename=filename, with_tree=False, only_header=True)

def test_header_entity_fields():
    with pytest.raises(ValidationError):
        parse(filename='fixtures/fail_too_many_header_entity_fields.ifc', only_header=True)

def test_header_entity_fields_whole_file():
    with pytest.raises(ValidationError):
        parse(filename='fixtures/fail_too_many_header_entity_fields.ifc')
        
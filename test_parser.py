import glob
import pytest

from main import parse, ValidationError
from contextlib import nullcontext

@pytest.mark.parametrize("file", glob.glob("fixtures/*.ifc"))
def test_file(file):
    if "fail_" in file:
        cm = pytest.raises(ValidationError)
    else:
        cm = nullcontext()

    with cm: 
        parse(filename=file)

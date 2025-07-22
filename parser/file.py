import types
import re 
import numbers
import itertools

from .parse import parse, ParseResult
from .grammar import HEADER_FIELDS
from .transformer import entity_instance

try:
    from .mvd_info import MvdInfo, LARK_AVAILABLE
except ImportError: # in case of running module locally (e.g. test_parser.py)
    from mvd_info import MvdInfo, LARK_AVAILABLE

class file:
    """
    A somewhat compatible interface (but very limited) to ifcopenshell.file
    """

    def __init__(self, result:ParseResult):
        self.header_ = result.header
        self.data_ = result.entities

    @property
    def schema_identifier(self) -> str:
        return self.header_["FILE_SCHEMA"][0][0]

    @property
    def schema(self) -> str:
        """General IFC schema version: IFC2X3, IFC4, IFC4X3."""
        prefixes = ("IFC", "X", "_ADD", "_TC")
        reg = "".join(f"(?P<{s}>{s}\\d+)?" for s in prefixes)
        match = re.match(reg, self.schema_identifier)
        version_tuple = tuple(
            map(
                lambda pp: int(pp[1][len(pp[0]) :]) if pp[1] else None,
                ((p, match.group(p)) for p in prefixes),
            )
        )
        return "".join(
            "".join(map(str, t)) if t[1] else ""
            for t in zip(prefixes, version_tuple[0:2])
        )

    @property
    def schema_version(self) -> tuple[int, int, int, int]:
        """Numeric representation of the full IFC schema version.

        E.g. IFC4X3_ADD2 is represented as (4, 3, 2, 0).
        """
        schema = self.wrapped_data.schema
        version = []
        for prefix in ("IFC", "X", "_ADD", "_TC"):
            number = re.search(prefix + r"(\d)", schema)
            version.append(int(number.group(1)) if number else 0)
        return tuple(version)


    @property
    def header(self):
        header = {}
        for field_name, namedtuple_class in HEADER_FIELDS.items():
            field_data = self.header_.get(field_name.upper(), [])
            header[field_name.lower()] = namedtuple_class(*field_data)

        return types.SimpleNamespace(**header)
    
    
    @property
    def mvd(self):
        if not LARK_AVAILABLE or MvdInfo is None:
            return None
        return MvdInfo(self.header)

    def __getitem__(self, key: numbers.Integral) -> entity_instance:
        return self.by_id(key)

    def by_id(self, id: int) -> entity_instance:
        """Return an IFC entity instance filtered by IFC ID.

        :param id: STEP numerical identifier
        :type id: int

        :raises RuntimeError: If `id` is not found or multiple definitions exist for `id`.

        :rtype: entity_instance
        """
        ns = self.data_.get(id, [])
        if len(ns) == 0:
            raise RuntimeError(f"Instance with id {id} not found")
        elif len(ns) > 1:
            raise RuntimeError(f"Duplicate definition for id {id}")
        return ns[0]

    def by_type(self, type: str) -> list[entity_instance]:
        """Return IFC objects filtered by IFC Type and wrapped with the entity_instance class.
        :rtype: list[entity_instance]
        """
        type_lc = type.lower()
        return list(
            filter(
                lambda ent: ent.type.lower() == type_lc,
                itertools.chain.from_iterable(self.data_.values()),
            )
        )

def open(fn, only_header= False) -> file:
    return file(parse(filename=fn, only_header=only_header))
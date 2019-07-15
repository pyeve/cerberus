import typing
from collections import abc, OrderedDict
from datetime import date, datetime
from types import MappingProxyType

from pytest import mark, raises

from cerberus import errors, SchemaError
from cerberus.base import normalize_rulesset
from cerberus.tests import assert_fail, assert_success


class SelfDefinedContainer(abc.Container):
    def __contains__(self, item):
        pass


class SelfDefinedType:
    pass


@mark.parametrize(
    ("_type", "value"),
    [
        ("boolean", 0),
        ("bytearray", b""),
        ("bytes", ""),
        ("ByteString", ""),
        ("Callable", True),
        ("complex", False),
        ("Container", 0),
        ("date", datetime(year=1945, month=5, day=9, hour=0, minute=1)),
        ("datetime", date(year=1945, month=5, day=9)),
        ("dict", OrderedDict),
        ("float", 1),
        ("frozenset", set()),
        ("Hashable", []),
        ("integer", 0.1),
        ("integer", False),
        ("Iterable", 0),
        ("Iterator", []),
        ("list", ()),
        ("Mapping", ((0, 1),)),
        ("MutableMapping", MappingProxyType({})),
        ("MutableSequence", ()),
        ("MutableSet", frozenset()),
        ("number", True),
        ("set", frozenset()),
        ("Set", ()),
        ("Sequence", set()),
        ("Sized", 0),
        ("string", b""),
        ("tuple", []),
        ("type", 0),
    ],
)
def test_type_fails(_type, value):
    assert_fail(
        schema={"field": {"type": _type}},
        document={"field": value},
        error=("field", ("field", 'type'), errors.TYPE, (_type,)),
    )


@mark.parametrize(
    ("_type", "value"),
    [
        ("boolean", True),
        ("bytearray", bytearray()),
        ("bytes", b""),
        ("ByteString", b""),
        ("Callable", assert_success),
        ("complex", complex(1, -1)),
        ("Container", []),
        ("Container", {}),
        ("Container", SelfDefinedContainer()),
        ("date", date(year=1945, month=5, day=9)),
        ("datetime", datetime(year=1945, month=5, day=9, hour=0, minute=1)),
        ("dict", {}),
        ("float", 0.1),
        ("frozenset", frozenset()),
        ("Hashable", 0),
        ("integer", 0),
        ("Iterable", []),
        ("Iterator", iter([])),
        ("list", []),
        ("Mapping", {}),
        ("MutableMapping", {}),
        ("MutableSequence", []),
        ("MutableSet", set()),
        ("number", 0),
        ("number", 0.0),
        ("Sequence", ()),
        ("set", set()),
        ("Set", frozenset()),
        ("Sized", ()),
        ("string", ""),
        ("tuple", ()),
        ("type", int),
    ],
)
def test_type_succeeds(_type, value):
    assert_success(schema={"field": {"type": _type}}, document={"field": value})


def test_type_skips_allowed():
    assert_fail(
        schema={'foo': {'type': 'string', 'allowed': ['a']}},
        document={'foo': 0},
        error=('foo', ('foo', 'type'), errors.TYPE, ('string',)),
    )


def test_type_skips_anyof():
    valid_parts = [
        {'schema': {'model number': {'type': 'string'}, 'count': {'type': 'integer'}}},
        {'schema': {'serial number': {'type': 'string'}, 'count': {'type': 'integer'}}},
    ]
    _errors = assert_fail(
        schema={'part': {'type': ['dict', 'string'], 'anyof': valid_parts}},
        document={'part': 10},
    )
    assert len(_errors) == 1


@mark.parametrize(
    ("test_function", "constraint", "value"),
    [
        (assert_success, list, []),
        (assert_success, abc.Sequence, []),
        (assert_success, str, ""),
        (assert_success, SelfDefinedType, SelfDefinedType()),
        (assert_fail, list, ()),
        (assert_fail, abc.Sequence, SelfDefinedType()),
        (assert_fail, str, 1.0),
        (assert_fail, SelfDefinedType, ""),
    ],
)
def test_type_with_class_as_constraint(test_function, constraint, value):
    test_function(schema={"field": {"type": constraint}}, document={"field": value})


def test_boolean_is_not_a_number():
    # https://github.com/pyeve/cerberus/issues/144
    assert_fail(schema={'value': {'type': 'number'}}, document={'value': True})


@mark.parametrize(
    ("origin_type", "expected_rules"),
    [
        (typing.Dict, {"type": (dict,)}),
        (
            typing.Dict[str, int],
            {
                "anyof": (
                    {
                        "type": (dict,),
                        "keysrules": {"type": (str,)},
                        "valuesrules": {"type": (int,)},
                    },
                )
            },
        ),
        (
            typing.List[str],
            {"anyof": ({"type": (list,), "itemsrules": {"type": (str,)}},)},
        ),
        (typing.Tuple, {"type": (tuple,)}),
        (
            typing.Tuple[int, str],
            {
                "anyof": (
                    {"type": (tuple,), "items": ({"type": (int,)}, {"type": (str,)})},
                )
            },
        ),
        (
            typing.Tuple[int, ...],
            {"anyof": ({"type": (tuple,), "itemsrules": {"type": (int,)}},)},
        ),
        (typing.Union[str, int], {"type": (str, int)}),
        (
            typing.Union[str, int, typing.Tuple[str, ...]],
            {
                "anyof": (
                    {"type": (tuple,), "itemsrules": {"type": (str,)}},
                    {"type": (str, int)},
                )
            },
        ),
        (typing.Optional[str], {"anyof": ({"type": (str,)}, {"nullable": True})}),
        (
            typing.Set["integer"],  # type: ignore
            {"anyof": ({"type": (set,), "itemsrules": {"type": ("integer",)}},)},
        ),
    ],
)
def test_normalization_of_generic_type_aliasses(origin_type, expected_rules, validator):
    assert normalize_rulesset({"type": origin_type}) == expected_rules
    validator.schema = {"foo": expected_rules}  # tests schema validation


def test_compound_type_and_anyof_is_invalid(validator):
    with raises(SchemaError):
        validator.schema = {"field": {"type": typing.Set[int], "anyof": []}}

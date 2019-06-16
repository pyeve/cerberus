from collections import abc, OrderedDict
from datetime import date, datetime

from pytest import mark

from cerberus import errors
from cerberus.tests import assert_fail, assert_success


class SelfDefinedType:
    pass


@mark.parametrize(
    ("_type", "value"),
    [
        ("boolean", 0),
        ("bytearray", b""),
        ("bytes", ""),
        ("complex", False),
        ("date", datetime(year=1945, month=5, day=9, hour=0, minute=1)),
        ("datetime", date(year=1945, month=5, day=9)),
        ("dict", OrderedDict),
        ("float", 1),
        ("frozenset", set()),
        ("integer", 0.1),
        ("integer", False),
        ("list", ()),
        ("number", True),
        ("set", frozenset()),
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
        ("complex", complex(1, -1)),
        ("date", date(year=1945, month=5, day=9)),
        ("datetime", datetime(year=1945, month=5, day=9, hour=0, minute=1)),
        ("dict", {}),
        ("float", 0.1),
        ("frozenset", frozenset()),
        ("integer", 0),
        ("list", []),
        ("number", 0),
        ("number", 0.0),
        ("set", set()),
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

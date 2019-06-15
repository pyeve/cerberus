from pytest import mark

from cerberus import errors
from cerberus.tests import assert_fail, assert_success


@mark.parametrize(
    ("field", "_type", "value"),
    [
        ('a_binary', 'binary', u"i'm not a binary"),
        ('a_boolean', 'boolean', "i'm not a boolean"),
        ('a_datetime', 'datetime', "i'm not a datetime"),
        ('a_dict', 'dict', "i'm not a dict"),
        ('a_float', 'float', "i'm not a float"),
        ('an_integer', 'integer', "i'm not an integer"),
        ('a_list_of_values', 'list', "i'm not a list"),
        ('a_number', 'number', "i'm not a number"),
        ('a_string', 'string', 1),
    ],
)
def test_type_fails(field, _type, value):
    assert_fail(
        document={field: value}, error=(field, (field, 'type'), errors.TYPE, _type)
    )


def test_type_succeeds():
    assert_success(document={'a_set': {'hello', 1}})


def test_type_skips_allowed():
    assert_fail(
        schema={'foo': {'type': 'string', 'allowed': ['a']}},
        document={'foo': 0},
        error=('foo', ('foo', 'type'), errors.TYPE, 'string'),
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


def test_boolean_is_not_a_number():
    # https://github.com/pyeve/cerberus/issues/144
    assert_fail(schema={'value': {'type': 'number'}}, document={'value': True})

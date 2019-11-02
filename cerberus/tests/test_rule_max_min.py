from datetime import date

from pytest import mark

from cerberus import errors
from cerberus.tests import assert_fail, assert_success


@mark.parametrize(
    ("field", "increment"), [("an_integer", 1), ("a_float", 1.0), ("a_number", 1)]
)
def test_max(schema, field, increment):
    max_value = schema[field]['max']
    value = max_value + increment
    assert_fail(
        {field: value}, error=(field, (field, 'max'), errors.MAX_VALUE, max_value)
    )


@mark.parametrize(
    ("field", "decrement"), [("an_integer", 1), ("a_float", 1.0), ("a_number", 1)]
)
def test_min(schema, field, decrement):
    min_value = schema[field]['min']
    value = min_value - decrement
    assert_fail(
        {field: value}, error=(field, (field, 'min'), errors.MIN_VALUE, min_value)
    )


def test_min_and_max_with_date():
    schema = {'date': {'min': date(1900, 1, 1), 'max': date(1999, 12, 31)}}
    assert_success({'date': date(1945, 5, 8)}, schema)
    assert_fail({'date': date(1871, 5, 10)}, schema)

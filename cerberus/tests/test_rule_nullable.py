from pytest import mark

from cerberus import errors
from cerberus.tests import assert_fail, assert_normalized, assert_success


@mark.parametrize(
    ("test_function", "document"),
    [
        (assert_success, {'a_nullable_integer': None}),
        (assert_success, {'a_nullable_integer': 3}),
        (assert_success, {'a_nullable_field_without_type': None}),
        (assert_fail, {'a_nullable_integer': "foo"}),
        (assert_fail, {'an_integer': None}),
        (assert_fail, {'a_not_nullable_field_without_type': None}),
    ],
)
def test_nullable(test_function, document):
    test_function(document=document)


def test_nullable_does_not_fail_coerce():
    assert_normalized(
        schema={'foo': {'coerce': int, 'nullable': True}},
        document={'foo': None},
        expected={'foo': None},
    )


def test_nullables_fail_coerce_on_non_null_values(validator):
    def failing_coercion(value):
        raise Exception("expected to fail")

    schema = {'foo': {'coerce': failing_coercion, 'nullable': True, 'type': 'integer'}}

    assert_normalized(document={'foo': None}, expected={'foo': None}, schema=schema)

    assert_fail(document={'foo': 2}, schema=schema, validator=validator)
    assert errors.COERCION_FAILED in validator._errors


def test_nullable_skips_allowed():
    assert_success(
        schema={'role': {'allowed': ['agent', 'client', 'supplier'], 'nullable': True}},
        document={'role': None},
    )


def test_nullable_skips_type(validator):
    assert_fail({'an_integer': None}, validator=validator)
    assert validator.errors == {'an_integer': ['null value not allowed']}
